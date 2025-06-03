from fastapi import APIRouter
from confluent_kafka import Consumer, Producer
from transformers import pipeline
import json

router = APIRouter()

@router.on_event("startup")
async def startup_event():
    consumer = Consumer({
        'bootstrap.servers': 'kafka:9092',
        'group.id': 'normalizer',
        'auto.offset.reset': 'earliest'
    })
    consumer.subscribe(['nubla-logs-*'])
    nlp = pipeline("text-classification")
    
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue
        
        log = json.loads(msg.value().decode('utf-8'))
        # Normalización con NLP
        log['classification'] = nlp(log['message'])[0]['label']
        # Enviar a Elasticsearch
        # (Implementar lógica para enviar a Elasticsearch)
        print(f"Normalized log: {log}")

@router.get("/health")
async def health():
    return {"status": "healthy"}