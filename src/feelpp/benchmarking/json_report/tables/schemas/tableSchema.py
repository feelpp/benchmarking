from typing import List, Dict, Optional, Literal, Union
from pydantic import BaseModel, Field, model_validator



class TableLayout(BaseModel):
    rename: Dict[str, str] = {}
    column_order: List[str] = []


class TableStyle(BaseModel):
    column_align: Dict[str,str] = {}
    column_width : Dict[str,int] = {}
    classnames: List[str] = []


class FilterInput(BaseModel):
    placeholder: Optional[str] = "Filter..."
    style:Optional[str] = "margin-bottom:0.5em;padding:0.3em;width:50%;"

