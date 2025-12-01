from pydantic import BaseModel, field_validator, model_validator, RootModel, ConfigDict, ValidationError
from typing import Literal, Union, Optional, List, Dict
from feelpp.benchmarking.reframe.schemas.parameters import Parameter
from feelpp.benchmarking.reframe.schemas.resources import Resources
from feelpp.benchmarking.reframe.schemas.scalability import Scalability
from feelpp.benchmarking.reframe.schemas.platform import Platform
from feelpp.benchmarking.reframe.schemas.defaultJsonReport import JsonReportSchemaWithDefaults,DefaultPlot
from feelpp.benchmarking.reframe.schemas.remoteData import RemoteData
import re

class Sanity(BaseModel):
    success:Optional[List[str]] = []
    error:Optional[List[str]] = []

class AdditionalFiles(BaseModel):
    description_filepath: Optional[str] = None
    parameterized_descriptions_filepath: Optional[str] = None
    custom_logs: Optional[List[str]] = []


class ConfigFile(BaseModel):
    executable: str
    timeout: Optional[str] = "0-00:05:00"
    resources: Optional[Resources] = Resources(tasks=1, exclusive_access=False)
    platforms:Optional[Dict[str,Platform]] = {"builtin":Platform()}
    use_case_name: str
    options: Optional[List[str]] = []
    env_variables:Optional[Dict] = {}
    remote_input_dependencies: Optional[Dict[str,RemoteData]] = {}
    input_file_dependencies: Optional[Dict[str,str]] = {}
    scalability: Optional[Scalability] = None
    sanity: Optional[Sanity] = Sanity()
    parameters: Optional[List[Parameter]] = []
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

