import logging
from services.rabbitmq import consume_rabbitmq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting RabbitMQ consumer...")
    consume_rabbitmq()