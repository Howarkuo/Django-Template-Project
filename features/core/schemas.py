from ninja import Schema
from pydantic import EmailStr
from pydantic import Field


class Http400BadRequestSchema(Schema):
    """Base schema for 400 response."""

    detail: str = "Bad Request"


class Http401UnauthorizedSchema(Schema):
    """Base schema for 401 response."""

    detail: str = "Unauthorized"


class Http403ForbiddenSchema(Schema):
    """Base schema for 403 response."""

    detail: str = "Forbidden"


class Http404NotFoundSchema(Schema):
    """Base schema for 404 response."""

    detail: str = "Not Found"


class BaseResponseSchema(Schema):
    """Base schema for response."""

    msg: str = "OK"


class AcceptInvitationRequestSchema(Schema):
    """Accept invitation request schema."""

    password: str
    token: str


class UserRegisterRequestSchema(Schema):
    """User register request schema."""

    email: str
    password: str
    password_confirm: str


class UserRegisterResponseSchema(Schema):
    """User register response schema."""

    email: str


class UserConfirmChangePasswordRequestSchema(Schema):
    """User change password schema."""

    old_password: str
    new_password: str
    token: int


class UserForgetPasswordRequestSchema(Schema):
    """User forget password schema."""

    email: EmailStr


class UserConfirmForgetPasswordRequestSchema(Schema):
    """User forget password schema."""

    email: EmailStr
    token: int
    password: str


class UserChangeEmailRequestSchema(Schema):
    """User change email schema."""

    email: EmailStr


class UserConfirmChangeEmailRequestSchema(Schema):
    """User change email schema."""

    email: EmailStr
    token: int


class CompanyRequestSchema(Schema):
    """Company request schema."""

    name: str
    telephone: str
    email: str
    address: str
    gui_number: str
    currency: str
    principle_name: str
    remark: str


class CompanyResponseSchema(Schema):
    """Get company response schema."""

    name: str
    telephone: str
    email: str
    address: str
    gui_number: str
    currency: str
    principle_name: str
    remark: str


class UserUpdateProfileRequestSchema(Schema):
    """User update profile request schema."""

    company_name: str = Field(default=None, description="公司名稱")
    name: str = Field(default=None, description="姓名")
    title: str = Field(default=None, description="職稱")


class UserGetProfileResponseSchema(Schema):
    """User get profile response schema."""

    company_name: str
    user_name: str
    title: str


class APIListsSchema(Schema):
    """API lists schema."""

    code: str
    name: str | None


class APIListsNumberSchema(Schema):
    """API lists number schema."""

    number: str
    name: str | None
