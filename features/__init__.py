import os
import sys
import warnings
from pathlib import Path

import uvicorn


warnings.filterwarnings("ignore")


def run():
    """Run django server."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

    sys.path.append(str(Path(__file__).parent.resolve()))

    uvicorn.run(
        app="config.asgi:application",
        host=os.environ.get("SERVER_HOST", default="127.0.0.1"),
        port=int(os.environ.get("SERVER_PORT", default=8000)),
        reload=True,
    )
