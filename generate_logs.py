import json
import random
from datetime import datetime, timedelta
import os

# Lista de tenants y dispositivos generados en schema.sql
tenants = [
    "acmecorp", "techinnovate", "globaltrade", "healthsolutions", "eduplatform",
    "retailchain", "finsecure", "logifreight", "mediastream", "energyworks"
]
devices = {
    "acmecorp": ["webserver-acme-001", "database-acme-002", "firewall-acme-003", "app-acme-004", "backup-acme-005"],
    "techinnovate": ["webserver-tech-001", "database-tech-002", "firewall-tech-003", "app-tech-004", "backup-tech-005"],
    "globaltrade": ["webserver-global-001", "database-global-002", "firewall-global-003", "app-global-004", "backup-global-005"],
    "healthsolutions": ["webserver-health-001", "database-health-002", "firewall-health-003", "app-health-004", "backup-health-005"],
    "eduplatform": ["webserver-edu-001", "database-edu-002", "firewall-edu-003", "app-edu-004", "backup-edu-005"],
    "retailchain": ["webserver-retail-001", "database-retail-002", "firewall-retail-003", "app-retail-004", "backup-retail-005"],
    "finsecure": ["webserver-fin-001", "database-fin-002", "firewall-fin-003", "app-fin-004", "backup-fin-005"],
    "logifreight": ["webserver-logi-001", "database-logi-002", "firewall-logi-003", "app-logi-004", "backup-logi-005"],
    "mediastream": ["webserver-media-001", "database-media-002", "firewall-media-003", "app-media-004", "backup-media-005"],
    "energyworks": ["webserver-energy-001", "database-energy-002", "firewall-energy-003", "app-energy-004", "backup-energy-005"]
}
actions = ["login", "logout", "file_access", "api_call", "db_query", "network_scan", "system_update", "error_report"]
statuses = ["success", "failure", "timeout", "denied"]
sources = ["10.0.0.1", "10.0.0.2", "10.0.0.3", "10.0.0.4", "10.0.0.5", "192.168.1.1", "192.168.1.2", "172.16.0.1"]

# Generar 10,000 logs
num_logs = 10000
logs = []

# Fecha de inicio: hace 7 días
start_time = datetime.now() - timedelta(days=7)

with open("logs/test.log", "w") as f:
    for i in range(num_logs):
        # Incrementar el tiempo en intervalos aleatorios (entre 1 segundo y 1 hora)
        time_increment = random.randint(1, 3600)  # Entre 1 segundo y 1 hora
        timestamp = start_time + timedelta(seconds=i * time_increment)
        
        # Seleccionar un tenant aleatorio
        tenant = random.choice(tenants)
        
        # Seleccionar un dispositivo aleatorio para ese tenant
        device = random.choice(devices[tenant])
        
        # Generar un user_id ficticio
        user_id = f"user_{random.randint(100, 999)}"
        
        # Generar el log
        log = {
            "timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "tenant_id": tenant,
            "device_id": device,
            "user_id": user_id,
            "action": random.choice(actions),
            "status": random.choice(statuses),
            "source": random.choice(sources)
        }
        # Escribir el log en el archivo
        f.write(json.dumps(log) + "\n")

print(f"Generated {num_logs} logs in logs/test.log")
