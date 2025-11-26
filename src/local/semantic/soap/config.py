"""SOAP client configuration."""

# pylint: disable=ungrouped-imports
try:
    from pydantic import Field
    from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover
    # Fallback for environments without pydantic-settings
    from pydantic import BaseModel as BaseSettings
    from pydantic import Field

    SettingsConfigDict = dict  # type: ignore[misc,assignment]


class SoapConfig(BaseSettings):  # type: ignore[misc]
    """SOAP client configuration from environment."""

    wsdl_url: str = Field(default="", description="WSDL endpoint URL")
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")
    cache_enabled: bool = Field(default=True, description="Enable WSDL caching")

    # Authentication
    username: str = Field(default="", description="Basic auth username")
    password: str = Field(default="", description="Basic auth password")
    api_key: str = Field(default="", description="API key header value")

    # WS-Security
    ws_security_enabled: bool = Field(default=False, description="Enable WS-Security")
    ws_security_username: str = Field(default="", description="WS-Security username")
    ws_security_password: str = Field(default="", description="WS-Security password")

    # Pydantic v2 settings config
    model_config = SettingsConfigDict(
        env_prefix="SOAP_",
        env_file=".env",
    )
