from pydantic import BaseModel, field_validator, model_validator, RootModel
from typing import Literal, Union, Optional, List, Dict
from feelpp.benchmarking.reframe.config.configParameters import Parameter

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

class Platform(BaseModel):
    type:Literal["builtin","apptainer","docker"]
    image:str
    options:List[str]

class ConfigFile(BaseModel):
    executable: str
    platform:Optional[Platform] = None
    use_case_name: str
    options: List[str]
    outputs: List[AppOutput]
    scalability: Scalability
    sanity: Sanity
    upload: Upload
    parameters: List[Parameter]
    plots: List[Plot]


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

class ExecutionConfigFile(RootModel):
    List[MachineConfig]