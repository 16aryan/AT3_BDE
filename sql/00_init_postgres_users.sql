-- Initialization script for PostgreSQL container: creates airflow user & database
CREATE ROLE airflow WITH LOGIN SUPERUSER PASSWORD 'airflow';
CREATE DATABASE airflow OWNER airflow;
GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;
