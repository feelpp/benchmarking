from pydantic import BaseModel, field_validator, model_validator, RootModel
from typing import Literal, Union, Optional, List
import shutil, os

class BaseRange(BaseModel):
    generator: Literal["double","linear","random","ordered"]
    mode: Literal["cores","step","list"]

class CoresRange(BaseRange):
    min_cores_per_node: int
    max_cores_per_node: int
    min_nodes: int
    max_nodes: int

    @field_validator("min_nodes","min_cores_per_node")
    @classmethod
    def checkMinValues(cls, v):
        """ Checks that min values are greater or eq than 1"""
        assert v >= 1, "Minimal values should be >= 1"
        return v

    @model_validator(mode="after")
    def checkMaxValues(self):
        """ Checks that max values are greater or eq than min values"""
        assert self.max_nodes >= self.min_nodes, "Max node number should be >= min"
        assert self.max_cores_per_node >= self.min_cores_per_node, "Max cores per node should be >= min"
        return self

    @field_validator("mode",mode="after")
    @classmethod
    def checkMode(cls,v):
        assert v == "cores", "Incorrect mode for Cores range"
        return v

class StepRange(BaseRange):
    min: Union[float,int]
    max: Union[float,int]

    step: Optional[Union[float,int]] = None
    n_steps: Optional[int] = None

    @field_validator("mode",mode="after")
    @classmethod
    def checkMode(cls,v):
        assert v == "step", "Incorrect mode for Step range"
        return v

class ListRange(BaseRange):
    sequence : List[Union[float,int,str]]

    @field_validator("mode",mode="after")
    @classmethod
    def checkMode(cls,v):
        assert v == "list", "Incorrect mode for List range"
        return v

    @field_validator("sequence",mode="before")
    @classmethod
    def checkMode(cls,v):
        assert len(v)>1, "Sequence must contain at least one element"
        return v

class Parameter(BaseModel):
    name:str
    active:Optional[bool] = True
    range: Union[CoresRange,StepRange,ListRange]


class Sanity(BaseModel):
    success:List[str]
    error:List[str]

class Stage(BaseModel):
    name:str
    file:str
    format:Literal["csv","tsv","json"]

class Scalability(BaseModel):
    directory: str
    stages: List[Stage]

class AppOutput(BaseModel):
    instance_path: str
    relative_filepath: str
    format: str

class Upload(BaseModel):
    active:Optional[bool] = True
    platform:Literal["girder","ckan"]
    folder_id: Union[str,int]


class PlotAxis(BaseModel):
    parameter: Optional[str] = None
    label:str

class Aggregation(BaseModel):
    column: str
    agg: Literal["sum","mean","min","max"]
class Plot(BaseModel):
    title:str
    plot_types:List[Literal["scatter","table","stacked_bar"]]
    transformation:Literal["performance","relative_performance","speedup"]
    aggregations:Optional[List[Aggregation]] = None
    variables:Optional[List[str]] = None
    names:List[str]
    xaxis:PlotAxis
    secondary_axis:Optional[PlotAxis] = None
    yaxis:PlotAxis
    color_axis:Optional[PlotAxis] = None


    @field_validator("xaxis","secondary_axis", mode="after")
    def checExecutableInstalled(cls, v):
        """ Checks that the parameter field is specified for xaxis and secondary_axis field"""
        if v:
            assert v.parameter is not None
        return v


class ConfigFile(BaseModel):
    executable: str
    use_case_name: str
    options: List[str]
    outputs: List[AppOutput]
    scalability: Scalability
    sanity: Sanity
    upload: Upload
    parameters: List[Parameter]
    plots: List[Plot]

    @field_validator('executable', mode="before")
    def checExecutableInstalled(cls, v):
        """ Check if executable is found on the system """
        if shutil.which(v) is None:
            raise ValueError(f"Executable not found or not installed: {v}")
        return v


    @model_validator(mode="after")
    def checkPlotAxisParameters(self):
        """ Checks that the plot axis parameter field corresponds to existing parameters"""
        for plot in self.plots:
            assert plot.xaxis.parameter in [ p.name for p in self.parameters], f"Xaxis parameter not found in parameter list: {plot.xaxis.parameter}"
            if plot.secondary_axis:
                assert plot.secondary_axis.parameter in [ p.name for p in self.parameters], f"Secondary axis parameter not found in parameter list: {plot.secondary_axis.parameter}"
            if plot.yaxis.parameter:
                assert plot.secondary_axis.parameter in [ p.name for p in self.parameters], f"Yaxis parameter not found in parameter list: {plot.yaxis.parameter}"
            if plot.color_axis and plot.color_axis.parameter:
                assert plot.secondary_axis.parameter in [ p.name for p in self.parameters], f"color parameter not found in parameter list: {plot.color_axis.parameter}"

        return self

class MachineConfig(BaseModel):
    machine:str
    active: Optional[bool] = True
    execution_policy:Literal["serial","async"]
    exclusive_access:bool
    valid_systems:List[str] = ["*"],
    valid_prog_environs:List[str] = ["*"]
    launch_options: List[str]
    reframe_base_dir:str
    reports_base_dir:str
    platform:str #TODO SET DEFAULT
    partition:str #TODO SET DEFAULT

class ExecutionConfigFile(RootModel):
    List[MachineConfig]