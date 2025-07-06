from fastapi import APIRouter
from confluent_kafka import Consumer
from elasticsearch import Elasticsearch
import json
import asyncio
import logging
import os
import time

router = APIRouter()
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

kafka_consumer_task = None

def get_kafka_consumer(max_retries=10, retry_delay=10):
    """Inicializa el consumidor de Kafka con reintentos."""
    for attempt in range(max_retries):
        try:
            consumer = Consumer({
                'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092'),
                'group.id': f"normalizer-{os.getenv('TENANT_ID', 'default')}",
                'auto.offset.reset': 'earliest',
                'enable.auto.commit': False,
                'fetch.max.bytes': 52428800,
                'client.id': 'nubla-normalizer'
            })
            logger.debug(f"Kafka consumer initialized successfully with bootstrap.servers={os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')}")
            return consumer
        except Exception as e:
            logger.error(f"Attempt {attempt + 1}/{max_retries} failed to initialize Kafka consumer: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise

def get_elasticsearch_client(max_retries=10, retry_delay=10):
    """Inicializa el cliente de Elasticsearch con reintentos."""
    for attempt in range(max_retries):
        try:
            client = Elasticsearch(
                hosts=[f"http://{os.getenv('ELASTICSEARCH_HOST', 'elasticsearch')}:9200"],
            )
            if client.ping():
                logger.debug("Connected to Elasticsearch successfully")
                return client
            else:
                logger.error("Failed to ping Elasticsearch")
                raise Exception("Elasticsearch ping failed")
        except Exception as e:
            logger.error(f"Attempt {attempt + 1}/{max_retries} failed to initialize Elasticsearch client: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise

def ensure_elasticsearch_index(es: Elasticsearch, index_name: str):
    """Asegura que el índice de Elasticsearch exista, creándolo si es necesario."""
    try:
        if not es.indices.exists(index=index_name):
            es.indices.create(
                index=index_name,
                body={
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0,
                        "index.lifecycle.name": "nubla-logs-policy"
                    },
                    "mappings": {
                        "properties": {
                            "message": {"type": "text"},
                            "tenant_id": {"type": "keyword"},
                            "time": {"type": "date", "format": "epoch_second"},
                            "tag": {"type": "keyword"}
                        }
                    }
                }
            )
            logger.info(f"Created Elasticsearch index: {index_name}")
        else:
            logger.debug(f"Elasticsearch index already exists: {index_name}")
    except Exception as e:
        logger.error(f"Failed to create Elasticsearch index {index_name}: {str(e)}")
        raise

async def consume_kafka():
    consumer = get_kafka_consumer()
    tenant_id = os.getenv("TENANT_ID", "default")
    topic = f"nubla-logs-{tenant_id}"
    
    # Verificar metadatos del tópico
    max_wait_attempts = 30
    wait_interval = 10
    for attempt in range(max_wait_attempts):
        try:
            metadata = consumer.list_topics(timeout=10)
            if topic in metadata.topics:
                logger.debug(f"Topic {topic} found in metadata: {metadata.topics[topic]}")
                break
            else:
                logger.warning(f"Topic {topic} not found in metadata, retrying...")
                if attempt < max_wait_attempts - 1:
                    await asyncio.sleep(wait_interval)
                else:
                    raise Exception(f"Topic {topic} not available after {max_wait_attempts} attempts")
        except Exception as e:
            logger.error(f"Attempt {attempt + 1}/{max_wait_attempts} failed to fetch metadata: {str(e)}")
            if attempt < max_wait_attempts - 1:
                await asyncio.sleep(wait_interval)
            else:
                raise
    
    consumer.subscribe([topic])
    logger.debug(f"Subscribed to topic: {topic}")
    
    es = get_elasticsearch_client()
    index_name = f"nubla-logs-{tenant_id}"
    ensure_elasticsearch_index(es, index_name)
    
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                logger.debug("No message received")
                await asyncio.sleep(1)
                continue
            if msg.error():
                logger.error(f"Kafka consumer error: {msg.error()}")
                continue
            
            try:
                log = json.loads(msg.value().decode('utf-8'))
                logger.debug(f"Raw message: {log}")
                
                es.index(index=index_name, body=log)
                logger.info(f"Indexed log in Elasticsearch: {index_name}")
                consumer.commit()
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Kafka consumer loop error: {str(e)}")
    finally:
        logger.info("Closing Kafka consumer")
        consumer.close()

@router.on_event("startup")
async def startup_event():
    global kafka_consumer_task
    if kafka_consumer_task is None:
        logger.debug("Starting Kafka consumer on application startup")
        kafka_consumer_task = asyncio.create_task(consume_kafka())

@router.get("/health")
async def health():
    logger.debug("Health endpoint called")
    return {"status": "healthy"}