from elasticsearch import Elasticsearch
from core.config import settings

def get_es():
    return Elasticsearch(f"http://{settings.elasticsearch_host}:9200")

def index_event(es: Elasticsearch, index: str, body: dict):
    es.index(index=index, document=body)