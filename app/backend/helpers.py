import logging

# Set up custom logging as we'll be intermixes with FastAPI/Uvicorn's logging
class ColoredLogFormatter(logging.Formatter):
    COLOR_CODES = {
        logging.DEBUG: "\033[94m",  # Blue
        logging.INFO: "\033[92m",  # Green
        logging.WARNING: "\033[93m",  # Yellow
        logging.ERROR: "\033[91m",  # Red
        logging.CRITICAL: "\033[95m",  # Magenta
    }
    RESET_CODE = "\033[0m"

    def format(self, record):
        color = self.COLOR_CODES.get(record.levelno, "")
        record.levelname = f"{color}{record.levelname}{self.RESET_CODE}"
        return super().format(record)


def logging_config():
    logging.basicConfig(
        level=logging.INFO,  # Set the logging level
        format="%(levelname)s:\t%(name)s - %(message)s",
        datefmt="%H:%M:%S",
    )

    # Override the formatter with the custom ColoredLogFormatter
    root_logger = logging.getLogger()  # Get the root logger
    for handler in root_logger.handlers:  # Iterate through existing handlers
        if handler.formatter:
            handler.setFormatter(ColoredLogFormatter(handler.formatter._fmt))