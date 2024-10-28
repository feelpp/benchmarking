from pydantic import BaseModel, field_validator, model_validator, RootModel
from typing import Literal, Union, Optional, List, Dict
from feelpp.benchmarking.reframe.config.configParameters import Parameter
from feelpp.benchmarking.reframe.config.configPlots import Plot


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
    filepath: str
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

class Image(BaseModel):
    protocol:Optional[Literal["oras","docker","library","local"]] = None
    name:str

    @model_validator(mode="after")
    def extractProtocol(self):
        """ Extracts the image protocol (oras, docker, etc..) or if a local image is provided.
        If local, checks if the image exists """

        if "://" in self.name:
            self.protocol = self.name.split("://")[0]
        else:
            self.protocol = "local"

        if self.protocol == "local":
            if not os.path.exists(self.name):
                raise FileNotFoundError(f"Image {self.name} not found")
        return self


class Platform(BaseModel):
    type:Literal["builtin","apptainer","docker"]
    image:Image
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
        parameter_names = [
            f"{outer.name}.{inner.name}" for outer in self.parameters if outer.zip
            for inner in outer.zip
        ] + [outer.name for outer in self.parameters if outer.sequence] + ["performance_variable"]
        for plot in self.plots:
            for ax in [plot.xaxis,plot.secondary_axis,plot.yaxis,plot.color_axis]:
                if ax and ax.parameter:
                    assert ax.parameter in parameter_names, f"Parameter not found {ax.parameter} in {parameter_names}"

        return self


class Container(BaseModel):
    platform: Literal["docker","apptainer"]
    cachedir:Optional[str] = None
    tmpdir:Optional[str] = None

    @field_validator("cachedir","tmpdir",mode="before")
    @classmethod
    def checkDirectories(cls,v):
        """Checks that the directories exists"""
        if v and not os.path.exists(v):
            raise FileNotFoundError(f"Cannot find {v}")

        return v

class MachineConfig(BaseModel):
    machine:str
    active: Optional[bool] = True
    execution_policy:Literal["serial","async"]
    partitions:List[str]
    valid_prog_environs:List[str] = ["*"]
    launch_options: List[str]
    reframe_base_dir:str
    reports_base_dir:str
    containers:Optional[List[Container]] = []


class ExecutionConfigFile(RootModel):
    List[MachineConfig]