from typing import List, Dict, Optional, Literal, Union
from pydantic import BaseModel, Field, model_validator



class TableLayout(BaseModel):
    rename: Optional[Dict[str, str]] = {}
    column_order: Optional[List[str]] = None


class TableStyle(BaseModel):
    column_align: Optional[Dict[str,str]] = {}
    column_width : Optional[Dict[str,int]] = {}
    classnames: Optional[List[str]] = []


class FilterInput(BaseModel):
    placeholder: Optional[str] = "Filter..."
    style:Optional[str] = "margin-bottom:0.5em;padding:0.3em;width:50%;"

