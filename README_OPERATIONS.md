```markdown
# Operaciones - Nubla SIEM

Resumen y procedimientos operativos útiles.

1) Snapshot (backup) rápido (dev)
- Crear snapshot manual:
  SNAPNAME="logs-default-$(date -u +%Y%m%dT%H%M%SZ | tr '[:upper:]' '[:lower:]')"
  curl -XPUT "http://localhost:9201/_snapshot/dev_backup/$SNAPNAME?wait_for_completion=true" \
    -H 'Content-Type: application/json' -d '{"indices":"logs-default-*","include_global_state":false}'

- Local repo configuration:
  - En docker-compose.yml: montar host:/tmp/es_snapshots -> /usr/share/opensearch/snapshots
  - Añadir en opensearch.yml: path.repo: ["/usr/share/opensearch/snapshots"]

2) Snapshots automáticos (ej. cron)
- Script: scripts/opensearch/snapshot_dev.sh (ejecutable).
- Cron example (root or opensearch runner): `0 0 * * * /path/to/repo/scripts/opensearch/snapshot_dev.sh >> /var/log/opensearch_snapshot.log 2>&1`

3) Consolidación / alias
- Ya consolidamos en `logs-default-consolidated-000001`.
- Alias `logs-default` now points to the consolidated index as write index.
- Rollback: restore from snapshot (commands in README).

4) ISM / Retention (recommended for production)
- Suggested ISM policy: `logs-default-retention` — rollover + delete after 7 days.
- Apply the policy via index templates or attach to newly created indices.

5) RabbitMQ / DLQ handling
- List queues: `curl -sS -u admin:securepass 'http://localhost:15672/api/queues' | jq .`
- Sample messages from DLQ:
  curl -sS -u admin:securepass -H 'Content-Type: application/json' -XPOST \
    'http://localhost:15672/api/queues/%2F/<dlq-name>/get' -d '{"count":5,"ackmode":"ack_requeue_false","encoding":"auto"}'

6) Healthchecks / metrics
- metrics-exporter uses a Python-based healthcheck in docker-compose.yml; keep it.
- Check metrics: `curl -sS http://localhost:9108/metrics | head -n 50`

7) Post-ops checklist
- Snapshot done and verified
- Reindex verified
- Alias swapped & smoke test validated
- Remove old indices only after snapshot confirmed
- Add ISM policy or schedule snapshots for production
```