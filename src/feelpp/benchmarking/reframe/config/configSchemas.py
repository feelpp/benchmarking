from pydantic import BaseModel, field_validator, model_validator, RootModel, ConfigDict, ValidationError
from typing import Literal, Union, Optional, List, Dict
from feelpp.benchmarking.reframe.config.configParameters import Parameter
from feelpp.benchmarking.json_report.figures.schemas.plot import Plot, PlotAxis
from feelpp.benchmarking.json_report.schemas.jsonReport import JsonReportSchema, DataFile
import os, re

class Sanity(BaseModel):
    success:Optional[List[str]] = []
    error:Optional[List[str]] = []

class Stage(BaseModel):
    name:str
    filepath:str
    format:Literal["csv","tsv","json"]
    variables_path:Optional[Union[str,List[str]]] = []
    units: Optional[Dict[str,str]] = {}

    @field_validator("units",mode="before")
    @classmethod
    def parseUnits(cls,v):
        v["*"] = v.get("*","s")
        return v

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
    clean_directory: Optional[bool] = False



class Image(BaseModel):
    url: Optional[str] = None
    filepath:str

    @field_validator("filepath", mode="after")
    @classmethod
    def checkImage(cls,v,info):
        if not info.data["url"] and not ("{{"  in v  or "}}" in v) :
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
    custom_logs: Optional[List[str]] = []


class Resources(BaseModel):
    tasks: Optional[Union[str,int]] = None
    tasks_per_node: Optional[Union[str,int]] = None
    gpus_per_node: Optional[Union[str,int]] = None
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

class BaseRemoteData(BaseModel):
    destination: str

class RemoteGirderData(BaseModel):
    item: Optional[str] = None
    file: Optional[str] = None
    folder: Optional[str] = None

    @model_validator(mode="after")
    def checkValidResource(self):
        if all(res is None for res in [self.item, self.file, self.folder]):
            raise ValueError("A valid resource needs to be specified, either 'file', 'folder' or 'item'")
        return self

class RemoteData(BaseRemoteData):
    girder: Optional[RemoteGirderData] = None

    @model_validator(mode="after")
    def checkRemoteDataPlatform(self):
        if all(plat is None for plat in [self.girder]):
            raise ValueError("A remote data platform should be specified, valid options are ['girder'] ")
        return self

class DefaultPlotYAxis(PlotAxis):
    parameter: Optional[str] = "value"
    label: Optional[str] = "Value"

class DefaultColorAxis(PlotAxis):
    parameter: Optional[str] = "perfvalue"
    label: Optional[str] = "Performance Variables"

class DefaultPlot(Plot):
    yaxis: DefaultPlotYAxis = DefaultPlotYAxis()
    color_axis: DefaultColorAxis = DefaultColorAxis()

class JsonReportSchemaWithDefaults(JsonReportSchema):
    data: List[Dict[str,str]] = [{
        "name":"reframe_report",
        "filepath":"./reframe_report.json",
        "preprocessor":"feelpp.benchmarking.report.plugins.reframeReport:runsToDfPreprocessor"
    }]

    @model_validator(mode="before")
    @classmethod
    def applyDefaultPlots(cls, values):
        """
        Automatically merges JSON plot items with DefaultPlot.
        """

        if not values:
            return values

        if isinstance(values, list):
            new_content = []
            for item in values:
                try:
                    node = { "type": "plot", "data":"reframe_report", "plot": DefaultPlot.model_validate(item) }
                except ValidationError:
                    node = item
                new_content.append(node)

            return {"content": new_content}

        elif isinstance(values, dict):
            if "content" in values and isinstance(values["content"], list):
                new_content = []
                for item in values["content"]:
                    if isinstance(item, dict) and item.get("type") == "plot":
                        item = {
                            "type": "plot",
                            "data":"reframe_report",
                            "plot": DefaultPlot.model_validate(item["plot"])
                        }
                    elif isinstance(item, dict) and item.get("type") == "section":
                        item = cls.applyDefaultPlots(item)
                    new_content.append(item)

                values["content"] = new_content

            return values

        else:
            raise TypeError(f"Expected dict or list at root, got {type(values)}")


    @model_validator(mode="after")
    def setDefaultTitle(self):
        if self.title is None:
            self.title = f"{self.datetime}"

        return self


class ConfigFile(BaseModel):
    executable: str
    timeout: str
    resources: Resources
    platforms:Optional[Dict[str,Platform]] = {"builtin":Platform()}
    output_directory:Optional[str] = ""
    use_case_name: str
    options: List[str]
    env_variables:Optional[Dict] = {}
    remote_input_dependencies: Optional[Dict[str,RemoteData]] = {}
    input_file_dependencies: Optional[Dict[str,str]] = {}
    scalability: Scalability
    sanity: Optional[Sanity] = Sanity()
    parameters: List[Parameter]
    additional_files: Optional[AdditionalFiles] = AdditionalFiles()
    json_report: Optional[Union[JsonReportSchemaWithDefaults,List[DefaultPlot]]] = JsonReportSchemaWithDefaults()

    model_config = ConfigDict( extra='allow' )
    def __getattr__(self, item):
        if item in self.model_extra:
            return self.model_extra[item]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{item}'")

    @field_validator("json_report", mode="before")
    @classmethod
    def coerce_report(cls, v):
        if not v:
            return JsonReportSchemaWithDefaults()
        if isinstance(v, list):
            return JsonReportSchemaWithDefaults.model_validate(v)
        return v

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

        parameter_names += [outer.name for outer in self.parameters if outer] + ["perfvalue","value"]

        for reportNode in self.json_report.flattenContent():
            if reportNode.type != "plot":
                continue
            plot = reportNode.plot
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

