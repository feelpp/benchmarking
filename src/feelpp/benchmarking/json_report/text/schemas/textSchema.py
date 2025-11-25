from typing import List, Dict, Optional, Literal, Union
from pydantic import BaseModel, Field, model_validator, field_validator
import re


DEFAULT_PLACEHOLDER_EXPR = r"@{([^}]+)}@"

class Text(BaseModel):
    mode: Optional[Literal["static","dynamic"]] = None
    content: str

    placeholder_expr:Optional[str] = DEFAULT_PLACEHOLDER_EXPR
    # raw: bool = False

    @model_validator(mode="before")
    @classmethod
    def coerceText(cls, values ):
        if isinstance(values,str):
            return {"content": values }

        if "content" not in values and "text" in values:
            values["content"] = values.pop("text")

        return values

    @model_validator(mode="after")
    def inferMode(self):
        if self.mode is None:
            self.mode = "dynamic" if re.search(self.placeholder_expr, self.content) else "static"
        return self
