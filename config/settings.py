from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Retell AI
    retell_api_key: str
    retell_agent_id: str
    retell_from_number: str

    # Scheduler
    scheduler_cron: str = "0 9 * * 1"  # Every Monday at 09:00

    # Contacts
    contacts_csv_path: str = "data/contacts/contacts.csv"

    # Recordings output directory
    recordings_dir: str = "data/recordings"


settings = Settings()
