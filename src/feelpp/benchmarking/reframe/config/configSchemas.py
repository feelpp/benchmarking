from pydantic import BaseModel, field_validator, model_validator, RootModel
from typing import Literal, Union, Optional, List, Dict
from feelpp.benchmarking.reframe.config.configParameters import Parameter
from feelpp.benchmarking.reframe.config.configPlots import Plot
import os

class Sanity(BaseModel):
    success:List[str]
    error:List[str]

class Stage(BaseModel):
    name:str
    file:str
    format:Literal["csv","tsv","json"]
    variables_path:Optional[str] = None

    @model_validator(mode="after")
    def checkFormatOptions(self):
        if self.format == "json":
            if self.variables_path == None:
                raise ValueError("variables_path must be specified if format == json")

            if "*" not in self.variables_path:
                raise ValueError("variables_path must contain a wildcard '*'")

        return self

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
    executable_dir: Optional[str] = None
    platform:Optional[Platform] = None
    output_directory:str
    use_case_name: str
    options: List[str]
    outputs: List[AppOutput]
    scalability: Scalability
    sanity: Sanity
    upload: Upload
    parameters: List[Parameter]
    plots: List[Plot]

    @field_validator("output_directory",mode="before")
    @classmethod
    def expandEnvVars(cls,v):
        """Expand environment variables on the values for path fields"""
        return os.path.expandvars(v)


    @model_validator(mode="after")
    def checkPlotAxisParameters(self):
        """ Checks that the plot axis parameter field corresponds to existing parameters"""
        parameter_names = []
        for outer in self.parameters:
            if outer.zip:
                for inner in outer.zip:
                    parameter_names.append(f"{outer.name}.{inner.name}")
            elif outer.sequence and all(type(s)==dict and s.keys() for s in outer.sequence):
                for inner in outer.sequence[0].keys():
                    parameter_names.append(f"{outer.name}.{inner}")

        parameter_names += [outer.name for outer in self.parameters if outer.sequence] + ["performance_variable"]
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