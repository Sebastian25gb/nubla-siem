-- /root/nubla-siem/seed.sql
INSERT INTO tenants (name) VALUES ('DelawareHotel'), ('AnotherTenant');
INSERT INTO users (tenant_id, username, password_hash, email) VALUES
  (1, 'user1', '$2b$12$/HROfmF1rK3XSPHuLhX0/e2WQlzgpHdgR8hrJGZwnHOKS2uYEsfLu', 'user1@delawarehotel.com'),
  (2, 'user2', '$2b$12$/HROfmF1rK3XSPHuLhX0/e2WQlzgpHdgR8hrJGZwnHOKS2uYEsfLu', 'user2@anothertenant.com');
INSERT INTO logs_access (user_id, tenant_id, access_level) VALUES
  (1, 1, 'read'),
  (2, 2, 'read');