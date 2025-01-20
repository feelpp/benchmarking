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
    variables_path:Optional[Union[str,List[str]]] = []

    @model_validator(mode="after")
    def checkFormatOptions(self):
        if self.format == "json":
            if not self.variables_path:
                raise ValueError("variables_path must be specified if format == json")
            if type(self.variables_path) == str:
                self.variables_path = [self.variables_path]
        elif self.format != "json":
            if self.variables_path:
                raise ValueError("variables_path cannot be specified with other format than json")
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

    @model_validator(mode="before")
    def extractProtocol(self):
        """ Extracts the image protocol (oras, docker, etc..) or if a local image is provided.
        If local, checks if the image exists """

        self["protocol"] = self["name"].split("://")[0] if "://" in self["name"] else "local"

        if self["protocol"] not in ["oras","docker","library","local"]:
            raise ValueError("Unkown Protocol")

        return self

    @field_validator("name", mode="after")
    @classmethod
    def checkImage(cls,v,info):
        if info.data["protocol"] == "local":
            if not os.path.exists(v):
                if info.context and info.context.get("dry_run", False):
                   print(f"Dry Run: Skipping image check for {v}")
                else:
                    raise FileNotFoundError(f"Cannot find image {v}")

        return v


class Platform(BaseModel):
    image:Optional[Image] = None
    input_dir:Optional[str] = None
    options:Optional[List[str]]= []
    append_app_options:Optional[List[str]]= []

class AdditionalFiles(BaseModel):
    description_filepath: Optional[str] = None
    parameterized_descriptions_filepath: Optional[str] = None


class Resources(BaseModel):
    tasks: Optional[Union[str,int]] = None
    tasks_per_node: Optional[Union[str,int]] = None
    nodes: Optional[Union[str,int]] = None
    memory: Optional[Union[str,int]] = 0
    exclusive_access: Optional[Union[str,bool]] = True

    @model_validator(mode="after")
    def validateResources(self):
        assert (
            self.tasks and self.tasks_per_node and not self.nodes or
            self.tasks_per_node and self.nodes and not self.tasks or
            self.tasks and not self.tasks_per_node and not self.nodes
        ), "Tasks - tasks_per_node - nodes combination is not supported"
        return self

class ConfigFile(BaseModel):
    executable: str
    timeout: str
    memory: Optional[str] = None
    resources: Resources
    platforms:Optional[Dict[str,Platform]] = {"builtin":Platform()}
    output_directory:Optional[str] = ""
    use_case_name: str
    options: List[str]
    env_variables:Optional[Dict] = {}
    outputs: List[AppOutput]
    scalability: Scalability
    sanity: Sanity
    parameters: List[Parameter]
    additional_files: Optional[AdditionalFiles] = None
    plots: Optional[List[Plot]] = []

    @field_validator("timeout",mode="before")
    @classmethod
    def validateTimeout(cls,v):
        pattern = r'^\d+-\d{1,2}:\d{1,2}:\d{1,2}$'
        if not re.match(pattern, v):
            raise ValueError(f"Time is not properly formatted (<days>-<hours>:<minutes>:<seconds>) : {v}")
        days,time = v.split("-")
        hours,minutes,seconds = time.split(":")

        assert int(days) >= 0
        assert 24>int(hours)>=0
        assert 60>int(minutes)>=0
        assert 60>int(seconds)>=0

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

        parameter_names += [outer.name for outer in self.parameters if outer] + ["performance_variable"]
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
            if k not in accepted_platforms:
                raise ValueError(f"{k} not implemented")
        return v

