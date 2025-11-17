from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from ninja import UploadedFile
from ninja_extra import api_controller
from ninja_extra import route
from ninja_extra.permissions import IsAuthenticated

from config.utils import get_image_type

from core.authentication import CustomJWTAuth

from . import exceptions
from . import schemas


@api_controller(prefix_or_class="user", tags=["user"])
class UserController:
    """User controller."""

    @route.get("/avatar", auth=CustomJWTAuth(), permissions=[IsAuthenticated])
    def get_self_avatar(self, request: WSGIRequest):
        """Get self avatar."""
        if request.user.avatar is None:  # type: ignore
            raise exceptions.Http404NotFoundException("The avatar does not exist.")

        avatar = bytes(request.user.avatar)  # type: ignore
        return HttpResponse(avatar, content_type=f"image/{get_image_type(avatar)}")

    @route.post("/avatar", response=schemas.BaseResponseSchema, auth=CustomJWTAuth(), permissions=[IsAuthenticated])
    def update_self_avatar(self, request: WSGIRequest, file: UploadedFile):
        """Update self avatar."""
        request.user.avatar = file.read()  # type: ignore
        request.user.save()
        return {"msg": "The avatar is updated."}

    @route.delete("/avatar", response=schemas.BaseResponseSchema, auth=CustomJWTAuth(), permissions=[IsAuthenticated])
    def delete_self_avatar(self, request: WSGIRequest):
        """Delete self avatar."""
        request.user.avatar = None  # type: ignore
        request.user.save()
        return {"msg": "The avatar is deleted."}
