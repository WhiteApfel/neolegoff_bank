from pythonjsonlogger import jsonlogger

LOGGING_LEVEL = "DEBUG"
DEBUG = 1


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": lambda: jsonlogger.JsonFormatter(
                "%(asctime)s %(levelname)s %(name)s %(funcName)s %(message)s"
                " %(pathname)s %(lineno)s"
            )
        },
        "string": {
            "format": (
                "%(asctime)s %(levelname)s %(name)s %(funcName)s %(message)s"
                " %(pathname)s %(lineno)s"
            )
        },
    },
    "handlers": {
        "console": {
            "class": "logging.FileHandler",
            "filename": "neolegoff.log",
            "formatter": "json",
            "level": LOGGING_LEVEL,
        },
        "debug_mode": {
            "class": "logging.StreamHandler",
            "formatter": "string",
            "level": "DEBUG",
        },
    },
    "loggers": {
        "neolegoff_bank": {
            "handlers": ["console" if DEBUG else "console", "debug_mode"],
            "level": "DEBUG",
        },
        "aiohttp.access": {"level": "WARNING"},
    },
}
