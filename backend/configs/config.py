import yaml
from pathlib import Path
from typing import Optional, Any
from pydantic import BaseModel, Field


class ApplicationConfig(BaseModel):
    name: str = "Legal Billing System"
    description: str = "A system to manage legal billing and invoicing."
    version: str = "1.0.0"
    debug: bool = True


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000


class SecurityConfig(BaseModel):
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440


class DatabaseConfig(BaseModel):
    url: str = "sqlite:///./data/legal_billing.db"


class JiraConfig(BaseModel):
    api_endpoint: str = "https://jira.bmw.com/rest/api/2"
    timeout: int = 30


class MicrosoftSSOConfig(BaseModel):
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None


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


class SMTPConfig(BaseModel):
    host: Optional[str] = None
    port: int = 587
    user: Optional[str] = None
    password: Optional[str] = None


class EmailConfig(BaseModel):
    smtp: SMTPConfig = Field(default_factory=SMTPConfig)
    from_address: str = Field(alias="from", default="noreply@altran.com")

    class Config:
        populate_by_name = True


class LoggingConfig(BaseModel):
    level: str = "INFO"
    file: str = "logs/app.log"


class Settings(BaseModel):
    """Application configuration settings loaded from YAML"""
    
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
    def load_from_yaml(cls, config_path: str = "config.yaml") -> "Settings":
        """Load settings from YAML file"""
        path = Path(config_path)
        
        if not path.exists():
            print(f"Warning: {config_path} not found, using default settings")
            return cls()
        
        with open(path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        return cls(**config_data)

    @classmethod
    def load_from_env_and_yaml(cls, config_path: str = "config.yaml") -> "Settings":
        """Load settings from YAML and override with environment variables"""
        import os
        
        # Load from YAML first
        settings = cls.load_from_yaml(config_path)
        
        # Override with environment variables if they exist
        # Database
        if db_url := os.getenv("DATABASE_URL"):
            settings.database.url = db_url
        
        # Security
        if secret_key := os.getenv("SECRET_KEY"):
            settings.security.secret_key = secret_key
        
        # SSO
        if os.getenv("SSO_ENABLED") is not None:
            settings.sso.enabled = os.getenv("SSO_ENABLED").lower() == "true"
        if tenant_id := os.getenv("MICROSOFT_TENANT_ID"):
            settings.sso.microsoft.tenant_id = tenant_id
        if client_id := os.getenv("MICROSOFT_CLIENT_ID"):
            settings.sso.microsoft.client_id = client_id
        if client_secret := os.getenv("MICROSOFT_CLIENT_SECRET"):
            settings.sso.microsoft.client_secret = client_secret
        
        # Email
        if smtp_host := os.getenv("SMTP_HOST"):
            settings.email.smtp.host = smtp_host
        if smtp_user := os.getenv("SMTP_USER"):
            settings.email.smtp.user = smtp_user
        if smtp_password := os.getenv("SMTP_PASSWORD"):
            settings.email.smtp.password = smtp_password
        
        return settings


# Create global settings instance
settings = Settings.load_from_env_and_yaml()


# Convenience properties for backward compatibility
class SettingsProxy:
    """Proxy to maintain backward compatibility with flat structure"""
    
    def __init__(self, settings: Settings):
        self._settings = settings
    
    # Application
    @property
    def APP_NAME(self) -> str:
        return self._settings.application.name
    
    @property
    def APP_VERSION(self) -> str:
        return self._settings.application.version
    
    @property
    def DEBUG(self) -> bool:
        return self._settings.application.debug
    
    # Server
    @property
    def HOST(self) -> str:
        return self._settings.server.host
    
    @property
    def PORT(self) -> int:
        return self._settings.server.port
    
    # Security
    @property
    def SECRET_KEY(self) -> str:
        return self._settings.security.secret_key
    
    @property
    def ALGORITHM(self) -> str:
        return self._settings.security.algorithm
    
    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        return self._settings.security.access_token_expire_minutes
    
    # Database
    @property
    def DATABASE_URL(self) -> str:
        return self._settings.database.url
    
    # Jira
    @property
    def JIRA_API_ENDPOINT(self) -> str:
        return self._settings.jira.api_endpoint
    
    @property
    def JIRA_TIMEOUT(self) -> int:
        return self._settings.jira.timeout
    
    # SSO
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
    
    # CORS
    @property
    def CORS_ORIGINS(self) -> list:
        return self._settings.cors.origins
    
    # Storage
    @property
    def UPLOAD_DIR(self) -> str:
        return self._settings.storage.upload_dir
    
    @property
    def MAX_UPLOAD_SIZE(self) -> int:
        return self._settings.storage.max_upload_size
    
    # Invoice
    @property
    def DEFAULT_CURRENCY(self) -> str:
        return self._settings.invoice.default_currency
    
    @property
    def INVOICE_PREFIX(self) -> str:
        return self._settings.invoice.prefix
    
    # Email
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
    
    # Logging
    @property
    def LOG_LEVEL(self) -> str:
        return self._settings.logging.level
    
    @property
    def LOG_FILE(self) -> str:
        return self._settings.logging.file


# Export both the structured settings and the backward-compatible proxy
config = SettingsProxy(settings)