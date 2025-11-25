import logging
from opensearchpy import OpenSearch

logger = logging.getLogger(__name__)

def ensure_tenant(es: OpenSearch, tenant_id: str, policy_id: str):
    alias = f"logs-{tenant_id}"
    index_initial = f"{alias}-000001"
    try:
        es.indices.get_alias(name=alias)
        logger.debug("alias_exists", extra={"tenant": tenant_id})
        return
    except Exception:
        logger.info("alias_missing_bootstrap", extra={"tenant": tenant_id})

    if not es.indices.exists(index=index_initial):
        es.indices.create(index=index_initial, body={
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "opendistro": {
                    "index_state_management": {
                        "rollover_alias": alias
                    }
                }
            }
        })
        logger.info("index_created", extra={"tenant": tenant_id, "index": index_initial})

    es.indices.put_alias(index=index_initial, name=alias, body={"is_write_index": True})
    es.indices.put_settings(index=index_initial, body={
        "index": {
            "opendistro.index_state_management.rollover_alias": alias
        }
    })
    try:
        es.transport.perform_request(
            "POST",
            f"/_plugins/_ism/add/{index_initial}",
            body={"policy_id": policy_id}
        )
        logger.info("policy_attach_ok", extra={"tenant": tenant_id, "policy_id": policy_id})
    except Exception as e:
        logger.warning("policy_attach_failed", extra={"tenant": tenant_id, "error": str(e)})