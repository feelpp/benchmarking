from typing import Literal, Union, Optional, List, Dict
from pydantic import BaseModel, field_validator, model_validator, RootModel

class PlotAxis(BaseModel):
    parameter: Optional[str] = None
    label:str

class Aggregation(BaseModel):
    column: str
    agg: str

    @field_validator("agg", mode="before")
    @classmethod
    def checkAgg(cls, v):
        if v not in ["sum","mean","min","max"] and not v.startswith("filter:"):
            raise NotImplementedError(f"Aggregation method {v} is not implemented.")
        return v

class Plot(BaseModel):
    title:str
    plot_types:List[Literal["scatter","table","stacked_bar","grouped_bar","heatmap"]]
    transformation:Literal["performance","relative_performance","speedup"]
    aggregations:Optional[List[Aggregation]] = None
    variables:Optional[List[str]] = None
    names:Optional[List[str]] = []
    xaxis:PlotAxis
    secondary_axis:Optional[PlotAxis] = None
    yaxis:PlotAxis
    color_axis:Optional[PlotAxis] = None
    layout_modifiers: Optional[Dict] = {}


    @field_validator("xaxis","secondary_axis", mode="after")
    @classmethod
    def checkAxis(cls, v):
        """ Checks that the parameter field is specified for xaxis and secondary_axis field"""
        if v:
            assert v.parameter is not None
        return v