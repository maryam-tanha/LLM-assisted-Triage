from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SSHConfig(BaseModel):
    host: str
    port: int = 22
    username: str
    key_path: str | None = None
    # repr=False prevents password from appearing in logs or stack traces
    password: str | None = Field(default=None, repr=False)
    timeout: int = 30

    model_config = ConfigDict(frozen=True)

    @field_validator("host", "username")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be empty")
        return v

    @field_validator("port")
    @classmethod
    def valid_port(cls, v: int) -> int:
        if not 1 <= v <= 65535:
            raise ValueError("port must be between 1 and 65535")
        return v

    @field_validator("timeout")
    @classmethod
    def positive_timeout(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("timeout must be positive")
        return v

    @model_validator(mode="after")
    def require_auth(self) -> "SSHConfig":
        if self.key_path is None and self.password is None:
            raise ValueError("Either key_path or password must be provided")
        return self
