-- PostgreSQL initialization script for Short Term Landlord
-- This script sets up the database schema and initial configuration

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Set timezone
SET timezone = 'UTC';

-- Create enum types for PostgreSQL
CREATE TYPE task_status AS ENUM ('pending', 'in_progress', 'completed', 'cancelled');
CREATE TYPE task_priority AS ENUM ('low', 'medium', 'high', 'urgent');
CREATE TYPE user_role AS ENUM ('admin', 'owner', 'cleaner', 'maintenance', 'guest');
CREATE TYPE invoice_status AS ENUM ('draft', 'sent', 'paid', 'overdue', 'cancelled');
CREATE TYPE repair_status AS ENUM ('reported', 'in_progress', 'completed', 'cancelled');
CREATE TYPE transaction_type AS ENUM ('stock_in', 'stock_out', 'adjustment');

-- Grant permissions to the landlord user
GRANT ALL PRIVILEGES ON DATABASE landlord_dev TO landlord;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO landlord;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO landlord;

-- Create default schema permissions
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO landlord;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO landlord;

-- Add comments for documentation
COMMENT ON DATABASE landlord_dev IS 'Short Term Landlord Property Management System';
COMMENT ON TYPE task_status IS 'Status of tasks in the system';
COMMENT ON TYPE user_role IS 'Roles available for system users';