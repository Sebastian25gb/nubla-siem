import logging
import time
from confluent_kafka import Consumer, KafkaError
from elasticsearch import Elasticsearch
import json

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de Kafka (defaults hardcodeados)
kafka_config = {
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'normalizer_group',
    'auto.offset.reset': 'earliest'
}

# Configuración de Elasticsearch (defaults hardcodeados)
es_config = {
    'host': 'elasticsearch',
    'port': 9200,
    'scheme': 'http'
}

# Configuración del tenant (default)
tenant_id = 'default'

def normalize_log(log):
    """Normaliza el log agregando el tenant_id."""
    try:
        log['tenant_id'] = tenant_id
        return log
    except Exception as e:
        logger.error(f"Error normalizing log: {e}")
        return None

def main():
    logger.info("Starting Kafka consumer and Elasticsearch client...")
    
    # Inicializar cliente de Elasticsearch
    es = Elasticsearch([{'host': es_config['host'], 'port': es_config['port'], 'scheme': es_config['scheme']}])
    
    # Verificar conexión a Elasticsearch
    if not es.ping():
        logger.error("Failed to connect to Elasticsearch")
        return
    
    # Inicializar consumidor de Kafka
    while True:
        try:
            consumer = Consumer(kafka_config)
            consumer.subscribe(['nubla-logs-default'])
            logger.info("Successfully subscribed to topic 'nubla-logs-default'")
            break
        except Exception as e:
            logger.error(f"Failed to subscribe to Kafka topic: {e}. Retrying in 5 seconds...")
            time.sleep(5)
    
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    logger.error(f"Kafka error: {msg.error()}. Retrying in 5 seconds...")
                    time.sleep(5)
                    continue
            
            # Procesar mensaje
            try:
                log = json.loads(msg.value().decode('utf-8'))
                normalized_log = normalize_log(log)
                if normalized_log:
                    es.index(index=f'nubla-logs-{tenant_id}', body=normalized_log)
                    logger.info(f"Indexed log in Elasticsearch: {normalized_log}")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
    
    except KeyboardInterrupt:
        logger.info("Shutting down consumer...")
    finally:
        consumer.close()

if __name__ == "__main__":
    main()
