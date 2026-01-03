import pydantic


class HealthCheckResponse(pydantic.BaseModel):
    status: str
