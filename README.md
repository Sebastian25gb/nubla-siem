# Nubla SIEM

A modern SIEM solution inspired by Splunk Enterprise Security, focused on scalability and security.

## Initial Setup

- **Base Services**: Zookeeper, Kafka, Logstash, Elasticsearch, PostgreSQL, and Redis have been set up using Docker Compose.
- **Zookeeper Configuration**: Using the official Zookeeper image (`zookeeper:3.8.0`). Port 2181 is exposed, and 4lw commands (`stat`, `ruok`, `mntr`) are enabled.
- **Log Ingestion**: Using Logstash (`docker.elastic.co/logstash/logstash:8.15.0`) to read logs from files and send them to Kafka.
- **Database Setup**: Initialized PostgreSQL with tables for `tenants`, `users`, and `devices`, including initial data for two tenants and four users.
- **Next Steps**: Configure a Spark consumer to process logs from Kafka and send them to Elasticsearch, and implement the backend with FastAPI.