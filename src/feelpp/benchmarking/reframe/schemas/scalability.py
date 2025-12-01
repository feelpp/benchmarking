from pydantic import model_validator,field_validator, BaseModel
from typing import Optional,Literal,Dict,Union,List


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
