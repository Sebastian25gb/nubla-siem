import pika
import os
import json
from confluent_kafka import Producer
import logging
import time

logger = logging.getLogger(__name__)

def get_rabbitmq_connection(max_retries=5, retry_delay=5):
    """Conecta a RabbitMQ con reintentos."""
    for attempt in range(max_retries):
        try:
            credentials = pika.PlainCredentials(
                os.getenv("RABBITMQ_USER", "admin"),
                os.getenv("RABBITMQ_PASSWORD", "securepass")
            )
            parameters = pika.ConnectionParameters(
                host=os.getenv("RABBITMQ_HOST", "rabbitmq"),
                port=5672,
                virtual_host="/",
                credentials=credentials,
                heartbeat=600
            )
            connection = pika.BlockingConnection(parameters)
            logger.debug("Connected to RabbitMQ successfully")
            return connection
        except Exception as e:
            logger.error(f"Attempt {attempt + 1}/{max_retries} failed to connect to RabbitMQ: {str(e)}. Retrying in {retry_delay} seconds...")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise

def get_kafka_producer(max_retries=5, retry_delay=5):
    """Inicializa el productor de Kafka con reintentos."""
    for attempt in range(max_retries):
        try:
            producer = Producer({
                'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092'),
                'client.id': 'nubla-rabbitmq-to-kafka',
                'acks': 1,
                'compression.type': 'gzip',
                'batch.size': 1024,
                'linger.ms': 5
            })
            logger.debug("Kafka producer initialized successfully")
            return producer
        except Exception as e:
            logger.error(f"Attempt {attempt + 1}/{max_retries} failed to create Kafka producer: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise

def callback(ch, method, properties, body):
    """Procesa mensajes de RabbitMQ y los publica en Kafka."""
    try:
        message = json.loads(body.decode('utf-8'))
        logger.info(f"Received message from RabbitMQ: {message}")
        producer = get_kafka_producer()
        tenant_id = message.get('tenant_id', os.getenv('TENANT_ID', 'default'))
        kafka_topic = f"nubla-logs-{tenant_id}"
        producer.produce(kafka_topic, json.dumps(message).encode('utf-8'))
        producer.flush()
        logger.info(f"Published message to Kafka topic {kafka_topic}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def consume_rabbitmq():
    """Consume mensajes de RabbitMQ y publícalos en Kafka."""
    while True:
        connection = None
        try:
            connection = get_rabbitmq_connection()
            channel = connection.channel()
            tenant_id = os.getenv("TENANT_ID", "default")
            queue = f"nubla_logs_{tenant_id}"
            exchange = f"logs_{tenant_id}"
            routing_key = f"nubla.log.{tenant_id}"

            channel.exchange_declare(exchange=exchange, exchange_type='topic', durable=True)
            channel.queue_declare(queue=queue, durable=True)
            channel.queue_bind(exchange=exchange, queue=queue, routing_key=routing_key)

            channel.basic_consume(queue=queue, on_message_callback=callback)
            logger.info(f"Starting to consume messages from RabbitMQ queue {queue}")
            channel.start_consuming()
        except (pika.exceptions.StreamLostError, pika.exceptions.ChannelWrongStateError, pika.exceptions.AMQPConnectionError) as e:
            logger.error(f"Connection or channel error: {str(e)}. Reconnecting...")
            time.sleep(5)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}. Reconnecting...")
            time.sleep(5)
        finally:
            if connection and not connection.is_closed:
                connection.close()
                logger.info("RabbitMQ connection closed")