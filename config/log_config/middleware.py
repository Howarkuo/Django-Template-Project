import logging
import time

from django.http import HttpRequest
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin


logger = logging.getLogger("uvicorn")


class APITimingMiddleware(MiddlewareMixin):
    """Middleware that calculates and logs the time taken to process each HTTP request."""

    def process_request(self, request: HttpRequest):
        """Records the start time of a request processing.

        Args:
            request (HttpRequest): The incoming HTTP request.
        """
        request.start_time = time.time()

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Logs the time taken to process the request upon sending the response.

        Args:
            request (HttpRequest): The request being processed.
            response (HttpResponse): The response being sent back.

        Returns:
            HttpResponse: The response object to be sent back.
        """
        if hasattr(request, "start_time"):
            elapsed_time = time.time() - request.start_time
            logger.info(
                "Request to API",
                extra={
                    "path": request.path,
                    "response_time": f"{elapsed_time:.2f}",
                    "ip": request.META.get("REMOTE_ADDR", "Unknown"),
                },
            )
        return response
