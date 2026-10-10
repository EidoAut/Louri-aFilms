import logging
from logging.handlers import RotatingFileHandler


def configure_logging(directory):
    handler = RotatingFileHandler(directory / "teleputin.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.WARNING)
    # HTTP request URLs may contain API keys. Never enable wire logging.
    logging.getLogger("httpx").setLevel(logging.CRITICAL)
    logging.getLogger("httpcore").setLevel(logging.CRITICAL)
