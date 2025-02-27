from typing import Literal, Union, Optional, List, Dict
from pydantic import BaseModel, field_validator, model_validator, RootModel
import os

class Container(BaseModel):
    cachedir:Optional[str] = None
    tmpdir:Optional[str] = None
    image_base_dir:str
    options:Optional[List[str]] = []

    @field_validator("cachedir","tmpdir","image_base_dir",mode="before")
    @classmethod
    def checkDirectories(cls,v, info):
        """Checks that the directories exists"""
        if v and not os.path.exists(v):
            if info.context.get("dry_run", False):
                print(f"Dry Run: Skipping directory check for {v}")
            else:
                raise FileNotFoundError(f"Cannot find {v}")

        return v

class MachineConfig(BaseModel):
    machine:str
    targets:Optional[Union[str,List[str]]] = None
    active: Optional[bool] = True
    execution_policy:Optional[Literal["serial","async"]] = "serial"
    reframe_base_dir:str
    reports_base_dir:str
    input_dataset_base_dir:Optional[str] = None
    input_user_dir:Optional[str] = None
    output_app_dir:str
    env_variables:Optional[Dict] = {}
    containers:Optional[Dict[str,Container]] = {}

    platform:Optional[Literal["apptainer","docker","builtin"]] = "builtin"
    partitions: Optional[List[str]] = []
    prog_environments: Optional[List[str]] = []

    #This field should be hidden from user schema ( are post-processed under parseTargets method )
    #TODO: maybe skipJsonSchema or something like that.
    environment_map: Optional[Dict[str,List[str]]] = {}

    @model_validator(mode="after")
    def parseTargets(self):
        if not self.targets:
            if not self.platform or not self.partitions or not self.prog_environments:
                raise ValueError("Either specify the `targets` field or the (platform, partitions,prog_environments) fields for a cartesian product.")
            return self

        self.targets = self.targets if type(self.targets) == list else [self.targets]
        platform = None

        for target in self.targets:

            split = target.split(":")
            if len(split) != 3:
                raise ValueError("Targets sould follow the syntax partition:plaform:environment")
            partition,plat,environment = split

            #Set default values
            if not partition:
                partition = "default"
            if not environment:
                environment = "default"
            if not plat:
                plat = "builtin"
            if plat not in ["apptainer","docker","builtin"]:
                raise ValueError(f"Platorm {plat} not supported")
            if not platform:
                platform = plat
            else:
                if platform != plat:
                    raise NotImplementedError(f"only specifying one platform is supported.")

            if partition not in self.environment_map:
                self.environment_map[partition] = []

            self.partitions.append(partition)
            self.prog_environments.append(environment)

            if environment not in self.environment_map[partition]:
                self.environment_map[partition].append(environment)

        self.platform = platform
        self.partitions = list(set(self.partitions))
        self.prog_environments = list(set(self.prog_environments))

        return self

    @field_validator("containers",mode="before")
    @classmethod
    def checkContainerTypes(cls,v):
        accepted_types = ["apptainer","docker"]
        for container_type in v.keys():
            assert container_type in accepted_types, f"{container_type} not implemented"
        return v

    @model_validator(mode="after")
    def checkInputUserDir(self):
        if self.input_user_dir:
            assert self.input_dataset_base_dir, "input_dataset_base_dir must be provided with input_user_dir"
            assert os.path.exists(self.input_user_dir) and os.path.isdir(self.input_user_dir), "Input User dir does not exist"
        return self

class ExecutionConfigFile(RootModel):
    List[MachineConfig]