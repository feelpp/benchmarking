from typing import Literal, Union, Optional, List, Dict
from pydantic import BaseModel, field_validator, model_validator

class PlotAxis(BaseModel):
    parameter: str
    label:Optional[str] = None
    filter:Optional[Union[str,list[str],dict[str,str],list[dict[str,str]]]] = []

    @field_validator("filter",mode="after")
    @classmethod
    def parseFilter(cls,v):
        # Case: val  → [{val: val}]
        if isinstance(v, str):
            return [{v: v}]

        # Case: [val]  → [{val: val}]
        if isinstance(v, list) and all(isinstance(i, str) for i in v):
            return [{i: i} for i in v]

        # Case: {val: custom}  → [{val: custom}]
        if isinstance(v, dict):
            return [v]

        # Case: [{val:custom}, {val2:custom2}]  → unchanged
        if isinstance(v, list) and all(isinstance(i, dict) for i in v):
            return v

        raise ValueError("Invalid filter format")


    @model_validator(mode="after")
    def defaultLabel(self):
        if self.label is None:
            self.label = self.parameter.title()
        return self

class Aggregation(BaseModel):
    column: str
    agg: str

    @field_validator("agg", mode="before")
    @classmethod
    def checkAgg(cls, v):
        if v not in ["sum","mean","min","max","first","count","nunique"] and not v.startswith("filter:"):
            raise NotImplementedError(f"Aggregation method {v} is not implemented.")
        return v

class Plot(BaseModel):
    title:str
    plot_types:List[Literal["scatter","table","stacked_bar","grouped_bar","heatmap","sunburst","scatter3d","surface3d","parallelcoordinates","marked_scatter"]]
    transformation:Optional[Literal["performance","relative_performance","speedup"]] = "performance"
    aggregations:Optional[List[Aggregation]] = None
    xaxis:PlotAxis
    secondary_axis:Optional[PlotAxis] = None
    yaxis:PlotAxis
    color_axis:Optional[PlotAxis] = None
    extra_axes:Optional[List[PlotAxis]] = []
    layout_modifiers: Optional[Dict] = {}

    @field_validator("xaxis","secondary_axis", mode="after")
    @classmethod
    def checkAxis(cls, v):
        """ Checks that the parameter field is specified for xaxis and secondary_axis field"""
        if v:
            assert v.parameter is not None
        return v