from fastapi import APIRouter, BackgroundTasks
from confluent_kafka import Consumer
from transformers import pipeline
import json
import asyncio
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

async def consume_kafka():
    consumer = Consumer({
        'bootstrap.servers': 'kafka:9092',
        'group.id': 'normalizer',
        'auto.offset.reset': 'earliest'
    })
    consumer.subscribe(['nubla-logs-*'])
    nlp = pipeline("text-classification")
    
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                await asyncio.sleep(1)  # Evitar consumo excesivo de CPU
                continue
            if msg.error():
                logger.error(f"Consumer error: {msg.error()}")
                continue
            
            log = json.loads(msg.value().decode('utf-8'))
            log['classification'] = nlp(log['message'])[0]['label']
            logger.info(f"Normalized log: {log}")
    except Exception as e:
        logger.error(f"Kafka consumer error: {str(e)}")
    finally:
        consumer.close()

@router.get("/health")
async def health(background_tasks: BackgroundTasks):
    background_tasks.add_task(consume_kafka)  # Iniciar consumo en fondo
    return {"status": "healthy"}