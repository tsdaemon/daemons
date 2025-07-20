from fastapi import APIRouter
from pydantic import BaseModel
from loguru import logger

from daemons.config import Config

config = Config()
router = APIRouter(prefix="/argus")

class ArgusRequest(BaseModel):
    logs: str
    service_name: str
    host: str
    unit: str | None = None

@router.post("/")
async def argus(
    request: ArgusRequest,
):
    from daemons.agents.argus import Argus
    agent = Argus(
        model_id=config.model,
        verbose=False,
    )
    logger.info(f"Starting Argus with model {config.model}")
    
    result = agent.run(request.logs, request.host, request.service_name, request.unit)
    return {"result": result}