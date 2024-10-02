from pydantic import BaseModel, field_validator, model_validator
from typing import Literal, Union, Annotated
from annotated_types import Len
import shutil, os

#-----REFRAME-------------------#


#----------Parameters-------#
class BaseParameter(BaseModel):
    active: bool
    type: Literal["continuous","discrete"]

class Topology(BaseModel):
    min_cores_per_node: int
    max_cores_per_node: int
    min_nodes: int
    max_nodes: int

    @field_validator("min_nodes","min_cores_per_node")
    @classmethod
    def checkMinValues(cls, v):
        assert v >= 1, "Minimal values should be >= 1"
        return v

    @model_validator(mode="after")
    def checkMaxValues(self):
        assert self.max_nodes >= self.min_nodes, "Max node number should be >= min"
        assert self.max_cores_per_node >= self.min_cores_per_node, "Max cores per node should be >= min"
        return self

class Sequencing(BaseModel):
    generator:Literal["default"]
    sequence:list[int]

class NbTasksParameter(BaseParameter):
    topology:Topology
    sequencing: Sequencing

class HsizeRange(BaseModel):
    min: float
    max: float

class MeshSizesParameter(BaseParameter):
    hsize_range: HsizeRange
    sequencing: Sequencing

class MeshesParameter(BaseParameter):
    pass

class SolversParameter(BaseParameter):
    pass

class Parameters(BaseModel):
    nb_tasks: NbTasksParameter
    mesh_sizes: MeshSizesParameter
    meshes: MeshesParameter
    solvers: SolversParameter

#---------------------------#

class ReframeDirectories(BaseModel):
    stage: str
    output: str

class Hosts(BaseModel):
    hostnames: Annotated[list[str], Len(min_length=1)]
    config_directory: str

    @field_validator("config_directory",mode="before")
    @classmethod
    def removeTrailingSlash(cls,v):
        if v[-1] == "/":
            v = v[:-1]
        return v

    @model_validator(mode="after")
    def checkFileExists(self):
        for hostname in self.hostnames:
            hostname_cfg_path = f"{self.config_directory}/{hostname}.py"
            assert os.path.exists(hostname_cfg_path), f"{hostname_cfg_path} does not exist"
        return self


class Reframe(BaseModel):
    exclusive_access:bool
    valid_systems: list[str]
    valid_prog_environs: list[str]
    policy:Literal["serial","async"]
    hosts: Hosts
    directories: ReframeDirectories
    parameters: Parameters

#--------------------------------#

#----------APPLICATION----------#

class Sanity(BaseModel):
    success:list[str]
    error:list[str]

class Stage(BaseModel):
    name:str
    file:str

class Scalability(BaseModel):
    directory: str
    stages: list[Stage]
    has_partial_performance:bool

class AppOutput(BaseModel):
    instance_path: str
    relative_filepath: str
    format: str

class Application(BaseModel):
    executable: str
    use_case_name: str
    options: list[str]
    outputs: list[AppOutput]
    scalability: Scalability
    sanity: Sanity

    @field_validator('executable', mode="before")
    def checExecutableInstalled(cls, v):
        if shutil.which(v) is None:
            raise ValueError(f"Executable not found or not installed: {v}")
        return v


#--------------------------------#

class ConfigFile(BaseModel):
    application : Application
    reframe: Reframe



