from pydantic import BaseModel
from pydantic import ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )
