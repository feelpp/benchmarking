from typing import Literal, Union, Optional, List, Dict
from pydantic import BaseModel, field_validator, model_validator, RootModel
import os

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
    input_dataset_base_dir:str
    output_app_dir:str
    containers:Optional[List[Container]] = []

class ExecutionConfigFile(RootModel):
    List[MachineConfig]