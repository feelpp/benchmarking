from typing import List, Dict, Optional, Literal, Union
from pydantic import BaseModel, Field, model_validator



class TableLayout(BaseModel):
    rename: Dict[str, str] = Field(default_factory=dict)
    column_order: List[str] = Field(default_factory=list)

