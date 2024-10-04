from pydantic import BaseModel, field_validator, model_validator, RootModel
from typing import Literal, Union, Annotated, Optional
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
        """ Checks that min values are greater or eq than 1"""
        assert v >= 1, "Minimal values should be >= 1"
        return v

    @model_validator(mode="after")
    def checkMaxValues(self):
        """ Checks that max values are greater or eq than min values"""
        assert self.max_nodes >= self.min_nodes, "Max node number should be >= min"
        assert self.max_cores_per_node >= self.min_cores_per_node, "Max cores per node should be >= min"
        return self

class Sequencing(BaseModel):
    generator:Literal["default","step","n_steps"]
    sequence:list[int]
    step: Optional[float|int] = None
    n_steps: Optional[int] = None


    @model_validator(mode="after")
    def checkGeneratorOptions(self):
        match self.generator:
            case "default": #Default discretization parametrization is step = (max - min) // 3
                self.n_steps = 3
            case "step":
                assert self.step is not None
            case "n_steps":
                assert self.n_steps is not None
            case _:
                raise ValueError("Unkown generator")
        return self

class NbTasksParameter(BaseParameter):
    topology:Topology
    sequencing: Sequencing

class HsizeRange(BaseModel):
    min: float
    max: float

class DiscretizationParameter(BaseParameter):
    hsize_range:Optional[HsizeRange] = None
    sequencing: Optional[Sequencing] = None
    meshes_filepaths: Optional[list[str]] = None

    @model_validator(mode="after")
    def checkTypeDataConsistency(self):
        if self.type == "continuous":
            assert self.meshes_filepaths is None and self.hsize_range is not None and self.sequencing is not None
        elif self.type == "discrete":
            assert self.meshes_filepaths is not None and self.hsize_range is None and self.sequencing is None
        return self

class SolversParameter(BaseParameter):
    @field_validator('type',mode="before")
    @classmethod
    def checkDiscrete(cls, v):
        """Fails if type!='discrete'"""
        assert v == "discrete", "Sovlers parameter must be of type discrete"
        return v

class Parameters(BaseModel):
    nb_tasks: NbTasksParameter
    discretization: DiscretizationParameter
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

class Upload(BaseModel):
    active:bool
    platform:Literal["girder","ckan"]
    folder_id:str | int


class ConfigFile(BaseModel):
    executable: str
    use_case_name: str
    options: list[str]
    outputs: list[AppOutput]
    scalability: Scalability
    sanity: Sanity
    upload: Upload
    parameters: Parameters

    @field_validator('executable', mode="before")
    def checExecutableInstalled(cls, v):
        """ Check if executable is found on the system """
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