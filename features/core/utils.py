import ast
import json
from datetime import date
from datetime import datetime
from datetime import timedelta
from operator import attrgetter
from operator import itemgetter
from types import ModuleType
from uuid import UUID

import boto3
from cryptography import fernet
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ImproperlyConfigured
from django.core.handlers.wsgi import WSGIRequest
from django.db import models
from django.db.utils import IntegrityError
from django.test import Client
from django.test import TestCase
from django_otp.oath import totp
from ninja import Schema
from ninja_extra import api_controller
from ninja_extra import route
from ninja_extra.ordering import Ordering
from ninja_extra.permissions import IsAuthenticated

from core.authentication import CustomJWTAuth
from core.models import BaseModel

from . import exceptions
from . import schemas


__encoder = fernet.Fernet(str(settings.FILE_INFO_SECRET_KEY).encode("utf-8"))


def __get_file_info_encode(file_info: dict) -> str:
    """Encodes and encrypts file information into a string.

    Args:
        file_info (dict): The file information to be encoded and encrypted.

    Returns:
        str: The encrypted string representation of the file information.
    """
    return __encoder.encrypt(str(file_info).encode("utf-8")).decode("utf-8")


def __get_file_info_decode(file_info_hash: str) -> dict:
    """Decrypts and decodes file information from a string.

    Args:
        file_info_hash (str): The encrypted string representation of the file information.

    Returns:
        dict: The decrypted and decoded file information.
    """
    decrypted_str = __encoder.decrypt(file_info_hash.encode("utf-8")).decode("utf-8")
    return ast.literal_eval(decrypted_str)


def get_s3_key(file_info: dict, file_name_key: str = "file_name") -> str:
    """Generates an S3 key for a file based on its information.

    Args:
        file_info (dict): The information about the file.
        file_name_key (str): The key in the file information dictionary that contains the file name.

    Returns:
        str: A string representing the S3 key for the file.
    """
    return f"{__get_file_info_encode(file_info)}.{file_info[file_name_key].split('.')[-1]}"


def get_file_info(s3_key: str) -> dict:
    """Retrieves file information from an S3 key.

    This function decodes the file information encoded in the S3 key. It splits the S3 key
    to extract the encoded file information and then decodes it to retrieve the original
    file information.

    Args:
        s3_key (str): The S3 key of the file, which contains encoded file information.

    Returns:
        dict: The decoded file information.
    """
    return __get_file_info_decode(s3_key.split(".")[0])


def get_year_month_from_date(data: date) -> date:
    """Retrieves the year and month from a date.

    Args:
        data (date): The date from which to retrieve the year and month.

    Returns:
        date: A date object representing the year and month of the input date.
    """
    return date(data.year, data.month, 1)


def verify_token(key: bytes, token: int, tolerance: int) -> bool:
    """Check if the totp token is valid in [-tolerance, 0] steps.

    Args:
        key (bytes): The key that TOTP used.
        token (int): The token that TOTP generated.
        tolerance (int): The tolerance that TOTP accept.

    Returns:
        bool: The token is verified.
    """
    return any(totp(key, drift=drift) == token for drift in range(-tolerance, 1))


def generate_crud_controller(
    model: type[BaseModel],
    model_name: str,
    controller_prefix: str,
    application_schemas: ModuleType,
):
    """Generate a CRUD controller for a model.

    Args:
        model (type[BaseModel]): The model for which to generate the CRUD controller.
        model_name (str): The name of the model.
        controller_prefix (str): The prefix for the controller.
        application_schemas (ModuleType): The module containing the application schemas.
    """

    @api_controller(
        prefix_or_class=controller_prefix,
        auth=CustomJWTAuth(),
        tags=[f"edit {model_name}"],
        permissions=[IsAuthenticated],
    )
    class CRUDController:
        Model = model

        @route.post(
            "",
            response={
                200: getattr(application_schemas, f"Get{model_name}ResponseSchema"),
                401: schemas.Http401UnauthorizedSchema,
            },
            permissions=[IsAuthenticated],
        )
        def create(
            self,
            request: WSGIRequest,
            body: getattr(application_schemas, f"Create{model_name}Schema"),  # type: ignore
        ) -> BaseModel:
            if isinstance(request.user, AnonymousUser):
                raise exceptions.Http401UnauthorizedException

            q = self.Model(**body.dict())

            try:
                q.create(request.user)
            except IntegrityError as e:
                raise exceptions.Http400BadRequestException("code already exists") from e

            return q

        @route.get(
            "",
            response={
                200: list[getattr(application_schemas, f"Get{model_name}ResponseSchema")],
                401: schemas.Http401UnauthorizedSchema,
            },
            permissions=[IsAuthenticated],
        )
        def get_all(
            self,
            request: WSGIRequest,
        ) -> list[BaseModel]:
            if isinstance(request.user, AnonymousUser):
                raise exceptions.Http401UnauthorizedException

            return self.Model.objects.filter(created_by_user=request.user).values()  # type: ignore

        @route.get(
            "/{pk}",
            response={
                200: getattr(application_schemas, f"Get{model_name}ResponseSchema"),
                401: schemas.Http401UnauthorizedSchema,
                404: schemas.Http404NotFoundSchema,
            },
            permissions=[IsAuthenticated],
        )
        def get(self, request: WSGIRequest, pk: UUID) -> BaseModel:
            if isinstance(request.user, AnonymousUser):
                raise exceptions.Http401UnauthorizedException

            try:
                q = self.Model.objects.get(id=pk)
            except self.Model.DoesNotExist as e:
                raise exceptions.Http404NotFoundException from e

            if q.company_id != request.user.company_id:  # type: ignore
                raise exceptions.Http403ForbiddenException("You don't have permission to get this object.")

            return q

        @route.put(
            "/{pk}",
            response={
                200: schemas.BaseResponseSchema,
                401: schemas.Http401UnauthorizedSchema,
                404: schemas.Http404NotFoundSchema,
            },
            permissions=[IsAuthenticated],
        )
        def update(
            self,
            request: WSGIRequest,
            pk: UUID,
            body: getattr(application_schemas, f"Put{model_name}Schema"),  # type: ignore
        ) -> dict:
            if isinstance(request.user, AnonymousUser):
                raise exceptions.Http401UnauthorizedException

            company_id = request.user.company_id  # type: ignore

            try:
                q = self.Model.objects.get(id=pk)
            except self.Model.DoesNotExist as e:
                raise exceptions.Http404NotFoundException from e

            if q.company_id != company_id:  # type: ignore
                raise exceptions.Http403ForbiddenException("You don't have permission to update this object.")

            for k, v in body.dict().items():
                setattr(q, k, v)

            try:
                q.save(request.user)
            except IntegrityError as e:
                raise exceptions.Http400BadRequestException("code already exists") from e

            return {"msg": "success"}

        @route.delete(
            "/{pk}",
            response={
                200: schemas.BaseResponseSchema,
                401: schemas.Http401UnauthorizedSchema,
                404: schemas.Http404NotFoundSchema,
            },
            permissions=[IsAuthenticated],
        )
        def delete(self, request: WSGIRequest, pk: UUID) -> dict:
            if isinstance(request.user, AnonymousUser):
                raise exceptions.Http401UnauthorizedException

            company_id = request.user.company_id  # type: ignore

            try:
                q = self.Model.objects.get(id=pk)
            except self.Model.DoesNotExist as e:
                raise exceptions.Http404NotFoundException from e

            if q.company_id != company_id:  # type: ignore
                raise exceptions.Http403ForbiddenException("You don't have permission to delete this object.")

            q.delete(request.user)

            return {"msg": "success"}

    return CRUDController


def create_basic_controller_test(model: type[BaseModel], url: str):
    """Create a basic controller test for a model."""

    class ControllerTest(TestCase):
        def setUp(self) -> None:
            self.url = f"/api/{url}"
            client = Client()
            response = client.post(
                "/api/auth/obtain",
                data=json.dumps({"email": settings.TEST_ACCOUNT_EMAIL, "password": settings.TEST_ACCOUNT_PASSWORD}),
                content_type="application/json",
            )
            jwt = response.json().get("access")
            self.client = Client(headers={"Authorization": f"Bearer {jwt}"})
            self.fields = model._meta.get_fields()[9:]  # noqa: SLF001
            self.instance = model.objects.get()

        @classmethod
        def setUpTestData(cls) -> None:
            user = models.User.objects.create_user(  # type: ignore
                username="test_account",
                email=settings.TEST_ACCOUNT_EMAIL,
                password=settings.TEST_ACCOUNT_PASSWORD,
            )
            fields = model._meta.get_fields()[9:]  # noqa: SLF001
            instance = model(**create_test_object(fields))  # type: ignore
            instance.create(user)

        def test_get(self) -> None:
            get_id = model.objects.get().id
            response = self.client.get(self.url + f"/{get_id}")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json().get("id"), str(get_id))

        def test_get_all(self) -> None:
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.json()), 1)

        def test_create(self) -> None:
            data = create_test_object(self.fields)  # type: ignore
            response = self.client.post(self.url, data, "application/json")
            self.assertEqual(response.status_code, 200)
            for field_name, field_value in data.items():
                self.assertEqual(str(response.json().get(field_name)), str(field_value))

        def test_update(self) -> None:
            update_data = create_update_fields(self.fields)  # type: ignore
            response = self.client.put(f"{self.url}/{self.instance.id}", update_data, "application/json")

            self.assertEqual(response.status_code, 200)

            self.instance.refresh_from_db()
            for field_name, update_value in update_data.items():
                current_value = getattr(self.instance, field_name)
                if isinstance(current_value, float) or isinstance(update_value, float):
                    self.assertEqual(float(current_value), float(update_value))
                else:
                    self.assertEqual(str(current_value), str(update_value))

        def test_delete(self) -> None:
            response = self.client.delete(f"{self.url}/{self.instance.id}")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(model.objects.count(), 0)

    return ControllerTest


def create_test_object(fields: list[models.Field]) -> dict:
    """Create a test object for a model."""
    test_data = {}

    for field in fields:
        match type(field):
            case models.CharField:
                test_data[field.name] = "tes"
            case models.TextField:
                test_data[field.name] = "tes"
            case models.IntegerField:
                test_data[field.name] = 1
            case models.BooleanField:
                test_data[field.name] = True
            case models.DateField:
                test_data[field.name] = datetime.now(tz=settings.TIME_ZONE).date()
            case models.DecimalField:
                test_data[field.name] = 1.0

    return test_data


def create_update_fields(fields: list[models.Field]) -> dict:
    """Create update fields for a model."""
    update_fields = {}

    for field in fields:
        match type(field):
            case models.CharField:
                update_fields[field.name] = "upd"
            case models.TextField:
                update_fields[field.name] = "upd"
            case models.IntegerField:
                update_fields[field.name] = 0
            case models.BooleanField:
                update_fields[field.name] = False
            case models.DateField:
                update_fields[field.name] = datetime.now(tz=settings.TIME_ZONE).date() + timedelta(days=1)
            case models.DecimalField:
                update_fields[field.name] = 2.00

    return update_fields


class OrderingWithDefault(Ordering):
    """Ordering with default values."""

    def __init__(
        self,
        schema: Schema,
        ordering_fields: list[str] | None = None,
        pass_parameter: str | None = None,
    ) -> None:
        """Initialize the OrderingWithDefault class."""
        super().__init__(ordering_fields=ordering_fields, pass_parameter=pass_parameter)
        self.schema = schema

    def ordering_queryset(
        self,
        items: models.QuerySet | list,
        ordering_input: Ordering.Input,
    ) -> models.QuerySet | list:
        """Order a queryset based on the input ordering."""
        ordering = self.get_ordering(items, ordering_input.ordering)
        if ordering:
            if isinstance(items, models.QuerySet):
                return items.order_by(*ordering)
            if isinstance(items, list) and items:

                def multisort(xs: list, specs: list[tuple[str, bool]]) -> list:
                    orerator = itemgetter if isinstance(xs[0], dict) else attrgetter
                    for key, reverse in reversed(specs):
                        getter = orerator(key)
                        field_info = self.schema.model_fields.get(key)
                        if field_info is None:
                            continue
                        default_value = field_info.default
                        xs.sort(key=lambda x: getter(x) or default_value, reverse=reverse)
                    return xs

                return multisort(items, [(o[int(o.startswith("-")) :], o.startswith("-")) for o in ordering])
        return items


def parse_key(key: str | bytes) -> fernet.Fernet:
    """If the key is a string we need to ensure that it can be decoded.

    :param key:
    :return:
    """
    return fernet.Fernet(key)


def get_crypter():
    """Get the MultiFernet object for the FIELD_ENCRYPTION_KEY setting."""
    configured_keys = getattr(settings, "FIELD_ENCRYPTION_KEY", None)

    if configured_keys is None:
        raise ImproperlyConfigured("FIELD_ENCRYPTION_KEY must be defined in settings")

    try:
        # Allow the use of key rotation
        if isinstance(configured_keys, tuple | list):
            keys = [parse_key(k) for k in configured_keys]
        else:
            # else turn the single key into a list of one
            keys = [parse_key(configured_keys)]
    except Exception as e:
        raise ImproperlyConfigured(f"FIELD_ENCRYPTION_KEY defined incorrectly: {e!s}") from e

    if len(keys) == 0:
        raise ImproperlyConfigured("No keys defined in setting FIELD_ENCRYPTION_KEY")

    return fernet.MultiFernet(keys)


CRYPTER = get_crypter()


def encrypt_str(s: str) -> bytes:
    """Encrypt a string using the FIELD_ENCRYPTION_KEY setting."""
    # be sure to encode the string to bytes
    return CRYPTER.encrypt(s.encode("utf-8"))


def decrypt_str(t: str) -> str:
    """Decrypt a string using the FIELD_ENCRYPTION_KEY setting."""
    # be sure to decode the bytes to a string
    return CRYPTER.decrypt(t.encode("utf-8")).decode("utf-8")


S3 = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)

SES = boto3.client(
    "ses",
    region_name=settings.AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)

BASE_EXCLUDE_FIELD = [
    "created_at",
    "created_by_user",
    "updated_at",
    "updated_by_user",
    "is_delete",
    "deleted_at",
    "deleted_by_user",
]

BASE_GET_EXCLUDE_FIELD = BASE_EXCLUDE_FIELD

BASE_UPDATE_EXCLUDE_FIELD = [*BASE_EXCLUDE_FIELD, "id"]

BASE_CREATE_EXCLUDE_FIELD = [*BASE_EXCLUDE_FIELD, "id"]
