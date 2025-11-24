from typing import List, Dict, Optional, Literal, Union
from pydantic import BaseModel, Field, model_validator


class FilterCondition(BaseModel):
    column: str
    op: Literal["==", "!=", ">", "<", ">=", "<=", "in", "not in"]
    value: object


class SortInstruction(BaseModel):
    column: str
    ascending: bool = True


class GroupBy(BaseModel):
    columns: List[str]
    agg: Union[Dict[str, str],str]


class Pivot(BaseModel):
    index: List[str]
    columns: List[str]
    values: str
    agg: str

class TableStyle(BaseModel):
    column_align: Dict[str,str] = {}
    column_width : Dict[str,int] = {}
    classnames: List[str] = []

class Table(BaseModel):
    columns: List[str] = Field(default_factory=list)
    rename: Dict[str, str] = Field(default_factory=dict)

    filter: List[FilterCondition] = Field(default_factory=list)
    sort: List[SortInstruction] = Field(default_factory=list)

    group_by: Optional[GroupBy] = None
    pivot: Optional[Pivot] = None

    format: Dict[str, Union[str,Dict[str,str]]] = Field(default_factory=dict)
    column_order: List[str] = Field(default_factory=list)

    style: Optional[TableStyle] = TableStyle()

    # -----------------------------
    # Validation logic (global)
    # -----------------------------
    @model_validator(mode="after")
    def validate_exclusivity(self):
        # Rule 1: pivot and group_by are mutually exclusive
        if self.group_by and self.pivot:
            raise ValueError(
                "Cannot use both 'group_by' and 'pivot' in a table. "
                "Pivot already performs aggregation, so 'group_by' is redundant."
            )

        # Rule 2: group_by must include agg
        if self.group_by:
            if not self.group_by.agg or len(self.group_by.agg) == 0:
                raise ValueError("'group_by' requires an 'agg' mapping.")

        # Rule 3: Sorting after pivot is ambiguous (optional but recommended)
        if self.pivot and self.sort:
            raise ValueError(
                "Sorting a pivoted table is ambiguous. Remove 'sort' or perform sorting before pivot."
            )

        return self
