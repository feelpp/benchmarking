from typing import Literal, Union, Optional, List, Dict
from pydantic import BaseModel, field_validator, model_validator, RootModel
import os

class Container(BaseModel):
    cachedir:Optional[str] = None
    tmpdir:Optional[str] = None
    image_base_dir:str

    @field_validator("cachedir","tmpdir","image_base_dir",mode="before")
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
    prog_environment:str = ["*"]
    reframe_base_dir:str
    reports_base_dir:str
    input_dataset_base_dir:str
    output_app_dir:str
    containers:Optional[Dict[str,Container]] = {}

    @field_validator("containers",mode="before")
    @classmethod
    def checkContainerTypes(cls,v):
        accepted_types = ["apptainer","docker"]
        for container_type in v.keys():
            assert container_type in accepted_types, f"{container_type} not implemented"
        return v
class ExecutionConfigFile(RootModel):
    List[MachineConfig]