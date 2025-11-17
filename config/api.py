from django.http import HttpRequest
from ninja.openapi.docs import Redoc
from ninja_extra import NinjaExtraAPI

from config.auth import AuthController

import core.apis as core_apis


api = NinjaExtraAPI(
    title="Ainsight Backend API",
    version="3.1.5",
    description="Ainsight Backend in django a.k.a. new structure",
    app_name="ainsight_backend",
    docs=Redoc(),
    docs_url="docs/",
)


@api.get("", tags=["health_check"])
async def api_root_health_check(request: HttpRequest):  # noqa: ARG001
    """Check api health."""
    return {"status": "healthy"}


@api.get("health_check/", tags=["health_check"])
async def health_check(request: HttpRequest):  # noqa: ARG001
    """Check api health."""
    return {"status": "healthy"}


api.register_controllers(AuthController)

# All EditController


# All QueryController


# All others controller
api.register_controllers(core_apis.UserController)
