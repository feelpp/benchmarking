from pydantic import BaseModel, field_validator, model_validator, RootModel
from typing import Literal, Union, Annotated
from annotated_types import Len
import shutil, os

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

class Sanity(BaseModel):
    success:list[str]
    error:list[str]

class Stage(BaseModel):
    name:str
    file:str
    format:Literal["csv","tsv","json"]

class Scalability(BaseModel):
    directory: str
    stages: list[Stage]

class AppOutput(BaseModel):
    instance_path: str
    relative_filepath: str
    format: str

class ConfigFile(BaseModel):
    executable: str
    use_case_name: str
    options: list[str]
    outputs: list[AppOutput]
    scalability: Scalability
    sanity: Sanity
    parameters: Parameters

    @field_validator('executable', mode="before")
    def checExecutableInstalled(cls, v):
        if shutil.which(v) is None:
            raise ValueError(f"Executable not found or not installed: {v}")
        return v


class MachineConfig(BaseModel):
    hostname:str
    active: bool
    execution_policy:Literal["serial","async"]
    exclusive_access:bool
    valid_systems:list[str] = ["*"],
    valid_prog_environs:list[str] = ["*"]
    launch_options: list[str]
    omp_num_threads: int
    reframe_base_dir:str
    reports_base_dir:str

class ExecutionConfigFile(RootModel):
    Annotated[list[MachineConfig], Len(min_length=1)]