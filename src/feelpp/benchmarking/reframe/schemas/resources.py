from pydantic import model_validator, BaseModel
from typing import Optional,Union

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