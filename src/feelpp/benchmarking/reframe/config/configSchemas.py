from pydantic import BaseModel, field_validator, model_validator, RootModel
from typing import Literal, Union, Optional, List, Dict
from feelpp.benchmarking.reframe.config.configParameters import Parameter
from feelpp.benchmarking.reframe.config.configPlots import Plot
import os, re

class Sanity(BaseModel):
    success:List[str]
    error:List[str]

class Stage(BaseModel):
    name:str
    filepath:str
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

class CustomVariable(BaseModel):
    name:str
    columns:List[str]
    op: Literal["sum","min","max","mean"]
    unit: str

class Scalability(BaseModel):
    directory: str
    stages: List[Stage]
    custom_variables:Optional[List[CustomVariable]] = []

class AppOutput(BaseModel):
    filepath: str
    format: str


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

        return self


class Platform(BaseModel):
    image:Optional[Image] = None
    input_dir:str
    options:Optional[List[str]]= []
    append_app_options:Optional[List[str]]= []

class ConfigFile(BaseModel):
    executable: str
    timeout: str
    platforms:Optional[Dict[str,Platform]] = None
    output_directory:str
    use_case_name: str
    options: List[str]
    outputs: List[AppOutput]
    scalability: Scalability
    sanity: Sanity
    parameters: List[Parameter]
    plots: Optional[List[Plot]] = []

    @field_validator("timeout",mode="before")
    @classmethod
    def validateTimeout(cls,v):
        pattern = r'^\d+-\d{1,2}:\d{1,2}:\d{1,2}$'
        if not re.match(pattern, v):
            raise ValueError(f"Time is not properly formatted (<days>-<hours>:<minutes>:<seconds>) : {v}")
        return v

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

    @field_validator("platforms",mode="before")
    @classmethod
    def checkPlatforms(cls,v):
        accepted_platforms = ["builtin","apptainer","docker"]
        for k in v.keys():
            assert k in accepted_platforms, f"{k} not implemented"
        return v

