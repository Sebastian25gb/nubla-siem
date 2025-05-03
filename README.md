# Nubla SIEM

A modern SIEM solution inspired by Splunk Enterprise Security, focused on scalability and security.

## Initial Setup

- **Base Services**: Zookeeper, Kafka, Elasticsearch, PostgreSQL, and Redis have been set up using Docker Compose.
- **Zookeeper Configuration**: Using the official Zookeeper image (`zookeeper:3.8.0`). Port 2181 is exposed, and 4lw commands (`stat`, `ruok`, `mntr`) are enabled.
- **Service Status**: All base services (Zookeeper, Kafka, Elasticsearch, PostgreSQL, Redis) are operational.
- **Next Steps**: Configure Fluentd for log ingestion and Kafka for message queuing.