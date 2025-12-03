import logging

from opensearchpy import OpenSearch

logger = logging.getLogger(__name__)


def ensure_default_tenant(es: OpenSearch):
    alias = "logs-default"
    index_initial = "logs-default-000001"
    try:
        es.indices.get_alias(name=alias)
        return
    except Exception:
        logger.info("alias_missing_bootstrap alias=logs-default")

    if not es.indices.exists(index=index_initial):
        es.indices.create(
            index=index_initial,
            body={
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "opendistro": {"index_state_management": {"rollover_alias": alias}},
                }
            },
        )
        logger.info("index_created index=%s", index_initial)

    es.indices.put_alias(index=index_initial, name=alias, body={"is_write_index": True})
    es.indices.put_settings(
        index=index_initial,
        body={"index": {"opendistro.index_state_management.rollover_alias": alias}},
    )
