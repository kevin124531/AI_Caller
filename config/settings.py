from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Retell AI
    retell_api_key: str
    retell_agent_id: str
    retell_from_number: str
    retell_webhook_secret: str = ""

    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/ai_caller"

    # S3
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    s3_bucket: str = "ai-caller-transcripts"

    # Scheduler
    scheduler_cron: str = "0 9 * * 1"  # Every Monday at 09:00

    # Contacts
    contacts_csv_path: str = "data/contacts/contacts.csv"

    # Server
    webhook_host: str = "0.0.0.0"
    webhook_port: int = 8000


settings = Settings()
