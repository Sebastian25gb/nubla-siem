from prometheus_client import Counter

INDEX_RETRIES = Counter("index_retries_total", "Número total de reintentos de indexación")