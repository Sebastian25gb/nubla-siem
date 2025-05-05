CREATE TABLE tenants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE devices (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(255) UNIQUE NOT NULL,
    tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertar tenants (10 empresas ficticias)
INSERT INTO tenants (name) VALUES 
('acmecorp'), 
('techinnovate'), 
('globaltrade'), 
('healthsolutions'), 
('eduplatform'), 
('retailchain'), 
('finsecure'), 
('logifreight'), 
('mediastream'), 
('energyworks');

-- Insertar usuarios (3 usuarios por tenant: 1 admin, 2 users)
-- Usa el hash generado para "yourpassword" en lugar de $2b$12$Kix2z9bN5f8gXgYbZ4z6QeW1Xy5jZ4z6QeW1Xy5jZ4z6QeW1Xy5jZ
INSERT INTO users (username, password_hash, role, tenant_id) VALUES 
-- AcmeCorp (tenant_id: 1)
('admin@acmecorp', '$2b$12$DRe/aIoS4dLMETqWCCuCDuP7X0rcJdnMpjeb1wVQobCzOZnHlps6i', 'admin', 1),
('user1@acmecorp', '$2b$12$DRe/aIoS4dLMETqWCCuCDuP7X0rcJdnMpjeb1wVQobCzOZnHlps6i', 'user', 1),
('user2@acmecorp', '$2b$12$DRe/aIoS4dLMETqWCCuCDuP7X0rcJdnMpjeb1wVQobCzOZnHlps6i', 'user', 1),
-- TechInnovate (tenant_id: 2)
('admin@techinnovate', '$2b$12$DRe/aIoS4dLMETqWCCuCDuP7X0rcJdnMpjeb1wVQobCzOZnHlps6i', 'admin', 2),
('user1@techinnovate', '$2b$12$DRe/aIoS4dLMETqWCCuCDuP7X0rcJdnMpjeb1wVQobCzOZnHlps6i', 'user', 2),
('user2@techinnovate', '$2b$12$DRe/aIoS4dLMETqWCCuCDuP7X0rcJdnMpjeb1wVQobCzOZnHlps6i', 'user', 2),
-- GlobalTrade (tenant_id: 3)
('admin@globaltrade', '$2b$12$DRe/aIoS4dLMETqWCCuCDuP7X0rcJdnMpjeb1wVQobCzOZnHlps6i', 'admin', 3),
('user1@globaltrade', '$2b$12$DRe/aIoS4dLMETqWCCuCDuP7X0rcJdnMpjeb1wVQobCzOZnHlps6i', 'user', 3),
('user2@globaltrade', '$2b$12$DRe/aIoS4dLMETqWCCuCDuP7X0rcJdnMpjeb1wVQobCzOZnHlps6i', 'user', 3),
-- HealthSolutions (tenant_id: 4)
('admin@healthsolutions', '$2b$12$DRe/aIoS4dLMETqWCCuCDuP7X0rcJdnMpjeb1wVQobCzOZnHlps6i', 'admin', 4),
('user1@healthsolutions', '$2b$12$DRe/aIoS4dLMETqWCCuCDuP7X0rcJdnMpjeb1wVQobCzOZnHlps6i', 'user', 4),
('user2@healthsolutions', '$2b$12$DRe/aIoS4dLMETqWCCuCDuP7X0rcJdnMpjeb1wVQobCzOZnHlps6i', 'user', 4),
-- EduPlatform (tenant_id: 5)
('admin@eduplatform', '$2b$12$DRe/aIoS4dLMETqWCCuCDuP7X0rcJdnMpjeb1wVQobCzOZnHlps6i', 'admin', 5),
('user1@eduplatform', '$2b$12$DRe/aIoS4dLMETqWCCuCDuP7X0rcJdnMpjeb1wVQobCzOZnHlps6i', 'user', 5),
('user2@eduplatform', '$2b$12$DRe/aIoS4dLMETqWCCuCDuP7X0rcJdnMpjeb1wVQobCzOZnHlps6i', 'user', 5),
-- RetailChain (tenant_id: 6)
('admin@retailchain', '$2b$12$DRe/aIoS4dLMETqWCCuCDuP7X0rcJdnMpjeb1wVQobCzOZnHlps6i', 'admin', 6),
('user1@retailchain', '$2b$12$DRe/aIoS4dLMETqWCCuCDuP7X0rcJdnMpjeb1wVQobCzOZnHlps6i', 'user', 6),
('user2@retailchain', '$2b$12$DRe/aIoS4dLMETqWCCuCDuP7X0rcJdnMpjeb1wVQobCzOZnHlps6i', 'user', 6),
-- FinSecure (tenant_id: 7)
('admin@finsecure', '$2b$12$DRe/aIoS4dLMETqWCCuCDuP7X0rcJdnMpjeb1wVQobCzOZnHlps6i', 'admin', 7),
('user1@finsecure', '$2b$12$DRe/aIoS4dLMETqWCCuCDuP7X0rcJdnMpjeb1wVQobCzOZnHlps6i', 'user', 7),
('user2@finsecure', '$2b$12$DRe/aIoS4dLMETqWCCuCDuP7X0rcJdnMpjeb1wVQobCzOZnHlps6i', 'user', 7),
-- LogiFreight (tenant_id: 8)
('admin@logifreight', '$2b$12$DRe/aIoS4dLMETqWCCuCDuP7X0rcJdnMpjeb1wVQobCzOZnHlps6i', 'admin', 8),
('user1@logifreight', '$2b$12$DRe/aIoS4dLMETqWCCuCDuP7X0rcJdnMpjeb1wVQobCzOZnHlps6i', 'user', 8),
('user2@logifreight', '$2b$12$DRe/aIoS4dLMETqWCCuCDuP7X0rcJdnMpjeb1wVQobCzOZnHlps6i', 'user', 8),
-- MediaStream (tenant_id: 9)
('admin@mediastream', '$2b$12$DRe/aIoS4dLMETqWCCuCDuP7X0rcJdnMpjeb1wVQobCzOZnHlps6i', 'admin', 9),
('user1@mediastream', '$2b$12$DRe/aIoS4dLMETqWCCuCDuP7X0rcJdnMpjeb1wVQobCzOZnHlps6i', 'user', 9),
('user2@mediastream', '$2b$12$DRe/aIoS4dLMETqWCCuCDuP7X0rcJdnMpjeb1wVQobCzOZnHlps6i', 'user', 9),
-- EnergyWorks (tenant_id: 10)
('admin@energyworks', '$2b$12$DRe/aIoS4dLMETqWCCuCDuP7X0rcJdnMpjeb1wVQobCzOZnHlps6i', 'admin', 10),
('user1@energyworks', '$2b$12$DRe/aIoS4dLMETqWCCuCDuP7X0rcJdnMpjeb1wVQobCzOZnHlps6i', 'user', 10),
('user2@energyworks', '$2b$12$DRe/aIoS4dLMETqWCCuCDuP7X0rcJdnMpjeb1wVQobCzOZnHlps6i', 'user', 10);

-- Insertar dispositivos (5 dispositivos por tenant)
INSERT INTO devices (device_id, tenant_id) VALUES 
-- AcmeCorp (tenant_id: 1)
('webserver-acme-001', 1),
('database-acme-002', 1),
('firewall-acme-003', 1),
('app-acme-004', 1),
('backup-acme-005', 1),
-- TechInnovate (tenant_id: 2)
('webserver-tech-001', 2),
('database-tech-002', 2),
('firewall-tech-003', 2),
('app-tech-004', 2),
('backup-tech-005', 2),
-- GlobalTrade (tenant_id: 3)
('webserver-global-001', 3),
('database-global-002', 3),
('firewall-global-003', 3),
('app-global-004', 3),
('backup-global-005', 3),
-- HealthSolutions (tenant_id: 4)
('webserver-health-001', 4),
('database-health-002', 4),
('firewall-health-003', 4),
('app-health-004', 4),
('backup-health-005', 4),
-- EduPlatform (tenant_id: 5)
('webserver-edu-001', 5),
('database-edu-002', 5),
('firewall-edu-003', 5),
('app-edu-004', 5),
('backup-edu-005', 5),
-- RetailChain (tenant_id: 6)
('webserver-retail-001', 6),
('database-retail-002', 6),
('firewall-retail-003', 6),
('app-retail-004', 6),
('backup-retail-005', 6),
-- FinSecure (tenant_id: 7)
('webserver-fin-001', 7),
('database-fin-002', 7),
('firewall-fin-003', 7),
('app-fin-004', 7),
('backup-fin-005', 7),
-- LogiFreight (tenant_id: 8)
('webserver-logi-001', 8),
('database-logi-002', 8),
('firewall-logi-003', 8),
('app-logi-004', 8),
('backup-logi-005', 8),
-- MediaStream (tenant_id: 9)
('webserver-media-001', 9),
('database-media-002', 9),
('firewall-media-003', 9),
('app-media-004', 9),
('backup-media-005', 9),
-- EnergyWorks (tenant_id: 10)
('webserver-energy-001', 10),
('database-energy-002', 10),
('firewall-energy-003', 10),
('app-energy-004', 10),
('backup-energy-005', 10);