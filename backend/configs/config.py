import yaml
import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class ApplicationConfig(BaseModel):
    name: str = "Legal Billing System"
    description: str = "A system to manage legal billing and invoicing."
    version: str = "1.0.0"
    debug: bool = True


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000


class SecurityConfig(BaseSettings):
    secret_key: str = Field(default="change-me-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    class Config:
        env_prefix = ""
        case_sensitive = False


class DatabaseConfig(BaseSettings):
    url: str = Field(default="sqlite:///./data/legal_billing.db")

    class Config:
        env_prefix = "DATABASE_"
        case_sensitive = False


class JiraConfig(BaseModel):
    api_endpoint: str = "https://jira.bmw.com/rest/api/2"
    timeout: int = 30


class MicrosoftSSOConfig(BaseSettings):
    tenant_id: Optional[str] = Field(default=None)
    client_id: Optional[str] = Field(default=None)
    client_secret: Optional[str] = Field(default=None)

    class Config:
        env_prefix = "MICROSOFT_"
        case_sensitive = False


class SSOConfig(BaseModel):
    enabled: bool = True
    provider: str = "microsoft"
    microsoft: MicrosoftSSOConfig = Field(default_factory=MicrosoftSSOConfig)


class CORSConfig(BaseModel):
    origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://billing.altran.com",
        "http://localhost:5173"
    ]


class StorageConfig(BaseModel):
    upload_dir: str = "./uploads"
    max_upload_size: int = 10 * 1024 * 1024


class InvoiceConfig(BaseModel):
    default_currency: str = "EUR"
    prefix: str = "INV"


class SMTPConfig(BaseSettings):
    host: Optional[str] = Field(default=None)
    port: int = 587
    user: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)

    class Config:
        env_prefix = "SMTP_"
        case_sensitive = False


class EmailConfig(BaseModel):
    smtp: SMTPConfig = Field(default_factory=SMTPConfig)
    from_address: str = Field(alias="from", default="noreply@altran.com")

    class Config:
        populate_by_name = True


class LoggingConfig(BaseModel):
    level: str = "INFO"
    file: str = "logs/app.log"


class Settings(BaseModel):
    """
    Application configuration settings.
    - Structural config loaded from config.yaml
    - Sensitive data loaded from .env file
    """
    
    application: ApplicationConfig = Field(default_factory=ApplicationConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    jira: JiraConfig = Field(default_factory=JiraConfig)
    sso: SSOConfig = Field(default_factory=SSOConfig)
    cors: CORSConfig = Field(default_factory=CORSConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    invoice: InvoiceConfig = Field(default_factory=InvoiceConfig)
    email: EmailConfig = Field(default_factory=EmailConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @classmethod
    def load(cls, config_path: str = ".config.yaml", env_file: str = ".env") -> "Settings":
        """
        Load settings from YAML (structural) and .env (secrets).
        Priority: .env > config.yaml > defaults
        """
        # Load .env file if it exists
        env_path = Path(env_file)
        if env_path.exists():
            from dotenv import load_dotenv
            load_dotenv(env_path)
        
        # Load structural config from YAML
        config_data = {}
        yaml_path = Path(config_path)
        if yaml_path.exists():
            with open(yaml_path, 'r') as f:
                config_data = yaml.safe_load(f) or {}
        else:
            print(f"Warning: {config_path} not found, using defaults")
        
        # Create base settings from YAML
        settings = cls(**config_data)
        
        # Override sensitive fields from environment variables
        # The BaseSettings subclasses will automatically read from env
        settings.security = SecurityConfig()
        settings.database = DatabaseConfig()
        settings.sso.microsoft = MicrosoftSSOConfig()
        settings.email.smtp = SMTPConfig()
        
        # Handle SSO_ENABLED from env
        if sso_enabled := os.getenv("SSO_ENABLED"):
            settings.sso.enabled = sso_enabled.lower() == "true"
        
        return settings


# Create global settings instance
settings = Settings.load()


class SettingsProxy:
    """Proxy to maintain backward compatibility with flat structure"""
    
    def __init__(self, settings: Settings):
        self._settings = settings
    
    @property
    def APP_NAME(self) -> str:
        return self._settings.application.name
    
    @property
    def APP_VERSION(self) -> str:
        return self._settings.application.version
    
    @property
    def DEBUG(self) -> bool:
        return self._settings.application.debug
    
    @property
    def HOST(self) -> str:
        return self._settings.server.host
    
    @property
    def PORT(self) -> int:
        return self._settings.server.port
    
    @property
    def SECRET_KEY(self) -> str:
        return self._settings.security.secret_key
    
    @property
    def ALGORITHM(self) -> str:
        return self._settings.security.algorithm
    
    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        return self._settings.security.access_token_expire_minutes
    
    @property
    def DATABASE_URL(self) -> str:
        return self._settings.database.url
    
    @property
    def JIRA_API_ENDPOINT(self) -> str:
        return self._settings.jira.api_endpoint
    
    @property
    def JIRA_TIMEOUT(self) -> int:
        return self._settings.jira.timeout
    
    @property
    def SSO_ENABLED(self) -> bool:
        return self._settings.sso.enabled
    
    @property
    def SSO_PROVIDER(self) -> str:
        return self._settings.sso.provider
    
    @property
    def MICROSOFT_TENANT_ID(self) -> Optional[str]:
        return self._settings.sso.microsoft.tenant_id
    
    @property
    def MICROSOFT_CLIENT_ID(self) -> Optional[str]:
        return self._settings.sso.microsoft.client_id
    
    @property
    def MICROSOFT_CLIENT_SECRET(self) -> Optional[str]:
        return self._settings.sso.microsoft.client_secret
    
    @property
    def CORS_ORIGINS(self) -> list:
        return self._settings.cors.origins
    
    @property
    def UPLOAD_DIR(self) -> str:
        return self._settings.storage.upload_dir
    
    @property
    def MAX_UPLOAD_SIZE(self) -> int:
        return self._settings.storage.max_upload_size
    
    @property
    def DEFAULT_CURRENCY(self) -> str:
        return self._settings.invoice.default_currency
    
    @property
    def INVOICE_PREFIX(self) -> str:
        return self._settings.invoice.prefix
    
    @property
    def SMTP_HOST(self) -> Optional[str]:
        return self._settings.email.smtp.host
    
    @property
    def SMTP_PORT(self) -> int:
        return self._settings.email.smtp.port
    
    @property
    def SMTP_USER(self) -> Optional[str]:
        return self._settings.email.smtp.user
    
    @property
    def SMTP_PASSWORD(self) -> Optional[str]:
        return self._settings.email.smtp.password
    
    @property
    def EMAIL_FROM(self) -> str:
        return self._settings.email.from_address
    
    @property
    def LOG_LEVEL(self) -> str:
        return self._settings.logging.level
    
    @property
    def LOG_FILE(self) -> str:
        return self._settings.logging.file


# Export both the structured settings and the backward-compatible proxy
config = SettingsProxy(settings)