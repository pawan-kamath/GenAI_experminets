# config.py
import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    # General Configurations
    DEBUG = True  # or False in production

    # OpenAI Configurations
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_API_HOST = os.getenv("OPENAI_API_HOST")

    # PostgreSQL Database Configurations
    POSTGRESQL_CONFIG = {
        "db_type": "postgresql",
        "host": os.getenv("POSTGRESQL_HOST"),
        "port": os.getenv("POSTGRESQL_PORT"),
        "database": os.getenv("POSTGRESQL_DATABASE"),
        "user": os.getenv("POSTGRESQL_USER"),
        "password": os.getenv("POSTGRESQL_PASSWORD"),
        "schema": os.getenv("POSTGRESQL_SCHEMA"),
    }

    # ServiceNow API Configurations
    SERVICENOW_CONFIG = {
        "db_type": "servicenow",
        "host": os.getenv("SERVICENOW_API_BASE_URL"),
        "user": os.getenv("SERVICENOW_USER"),
        "password": os.getenv("SERVICENOW_PASSWORD"),
    }
