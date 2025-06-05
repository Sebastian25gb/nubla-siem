from fastapi import APIRouter, BackgroundTasks
import pika
from transformers import pipeline
import json
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

async def consume_rabbitmq():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()
    channel.exchange_declare(exchange='logs', exchange_type='topic')
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange='logs', queue=queue_name, routing_key='nubla-logs.*')
    nlp = pipeline("text-classification")

    def callback(ch, method, properties, body):
        log = json.loads(body.decode('utf-8'))
        log['classification'] = nlp(log['message'])[0]['label']
        logger.info(f"Normalized log: {log}")

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

@router.get("/health")
def health(background_tasks: BackgroundTasks):
    background_tasks.add_task(consume_rabbitmq)
    return {"status": "healthy"}