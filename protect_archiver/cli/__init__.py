from .download import *  # NOQA
from .events import *  # NOQA
from .sync import *  # NOQA


def main() -> None:
    import logging
    import os

    import urllib3

    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)

    os.environ.setdefault("PYTHONUNBUFFERED", "true")

    # disable InsecureRequestWarning for unverified HTTPS requests
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    from .base import cli

    cli.main()
