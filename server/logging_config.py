# server/logging_config.py
import logging

# Configure global logging format and level
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# Logger instance for the module
logger = logging.getLogger(__name__)
