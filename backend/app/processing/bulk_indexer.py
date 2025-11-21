import logging
import time
from typing import Any, Dict, List, Optional

from opensearchpy import OpenSearch
from prometheus_client import Gauge, Histogram

logger = logging.getLogger(__name__)

INDEX_LATENCY = Histogram(
    "index_latency_seconds",
    "Latencia por flush bulk o documento individual",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0),
)
BUFFER_SIZE = Gauge("consumer_buffer_size", "Número de eventos en buffer bulk")


class BulkIndexer:
    """
    Buffer simple en memoria; flush por tamaño o intervalo.
    """

    def __init__(
        self,
        client: OpenSearch,
        max_items: int = 500,
        max_interval_ms: int = 1000,
        default_pipeline: Optional[str] = None,
    ):
        self.client = client
        self.max_items = max_items
        self.max_interval_ms = max_interval_ms
        self.default_pipeline = default_pipeline
        self.buffer: List[Dict[str, Any]] = []
        self.last_flush_ts = time.time()
        BUFFER_SIZE.set(0)

    def add(self, index: str, doc: Dict[str, Any], pipeline: Optional[str] = None):
        action = {
            "_index": index,
            "_source": doc,
        }
        if pipeline or self.default_pipeline:
            action["pipeline"] = pipeline or self.default_pipeline
        self.buffer.append(action)
        BUFFER_SIZE.set(len(self.buffer))
        now = time.time()
        if len(self.buffer) >= self.max_items or (
            (now - self.last_flush_ts) * 1000 >= self.max_interval_ms
        ):
            self.flush()

    def flush(self):
        if not self.buffer:
            return
        payload: List[Dict[str, Any]] = []
        for a in self.buffer:
            # Formato bulk API: acción + documento
            header = {"index": {"_index": a["_index"]}}
            if "pipeline" in a:
                header["index"]["pipeline"] = a["pipeline"]
            payload.append(header)
            payload.append(a["_source"])

        start = time.time()
        try:
            resp = self.client.bulk(body=payload, refresh=False)
            took = time.time() - start
            INDEX_LATENCY.observe(took)
            errors = resp.get("errors")
            if errors:
                logger.warning("bulk_flush_partial_errors", extra={"items": len(self.buffer)})
            else:
                logger.info(
                    "bulk_flush_ok", extra={"items": len(self.buffer), "took_seconds": took}
                )
        except Exception as e:
            logger.exception(
                "bulk_flush_failed", extra={"items": len(self.buffer), "error": str(e)}
            )
            # No vaciamos buffer para posible reintento simple (descartamos por simplicidad aquí)
        finally:
            self.buffer.clear()
            BUFFER_SIZE.set(0)
            self.last_flush_ts = time.time()
