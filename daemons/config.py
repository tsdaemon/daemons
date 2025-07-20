from pydantic_settings import BaseSettings


class Config(BaseSettings):
    model: str
    verbose: bool = False

    class Config:
        env_prefix = "DAEMONS_"
