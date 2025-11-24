from prometheus_client import Counter

# Contador de reintentos de indexación
INDEX_RETRIES = Counter("index_retries_total", "Número total de reintentos de indexación")
