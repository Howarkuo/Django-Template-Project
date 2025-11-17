import os
import sys
import time
import warnings
from pathlib import Path

import django
import psycopg2
import uvicorn
from django.conf import settings


warnings.filterwarnings("ignore")


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

    current_path = Path(__file__).parent.resolve()
    sys.path.append(str(current_path / "features"))

    suggest_unrecoverable_after = 30
    start = time.time()

    django.setup()

    while True:
        try:
            psycopg2.connect(
                host=settings.DATABASES["default"]["HOST"],
                port=settings.DATABASES["default"]["PORT"],
                user=settings.DATABASES["default"]["USER"],
                password=settings.DATABASES["default"]["PASSWORD"],
                dbname=settings.DATABASES["default"]["NAME"],
            )
            break
        except psycopg2.OperationalError as error:
            sys.stderr.write("Waiting for PostgreSQL to become available...\n")

            if time.time() - start > suggest_unrecoverable_after:
                sys.stderr.write(
                    f"   This is taking longer than expected. The following exception may be indicative of an unrecoverable error: \n   {error}\n"
                )

        time.sleep(1)

    uvicorn.run(
        app="config.asgi:application",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=True,
    )
