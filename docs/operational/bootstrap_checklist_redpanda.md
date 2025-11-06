# Checklist de bootstrap — Redpanda (Kafka API)

1) Seguridad
- Habilitar TLS para brokers y Schema Registry.
- Configurar SASL/SCRAM para productores/consumidores.
- Definir ACLs por topics y prefijos (principio de mínimo privilegio).

2) Topics y retención
- Crear topics: logs.v1, dlq.v1, detections.v1, playbooks.v1.
- Definir particiones según EPS esperado y cardinalidad de entidades.
- Establecer retención por tiempo/tamaño adecuada para replays razonables.

3) Schema Registry
- Publicar NCS v1 (JSON Schema) como contrato.
- Establecer compatibilidad backward/forward según política.
- Rechazo de mensajes que no cumplen schema (validación en productores/gateway).

4) Observabilidad
- Dashboards de lag, throughput, errores, particiones desbalanceadas.
- Alertas por lag p95, tasa de errores y saturación de disco.

5) Operación
- Procedimientos de rotación de credenciales y certificados.
- Política de naming y versionado de topics (sufijo .vN).