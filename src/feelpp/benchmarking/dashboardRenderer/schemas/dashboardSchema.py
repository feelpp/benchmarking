from pydantic import BaseModel, field_validator
from typing import List, Dict, Optional, Union


class LeafTemplateData(BaseModel):
    prefix: Optional[str] = ""
    format: str = None
    action: Optional[str] = "input"

class LeafTemplateDataFile(LeafTemplateData):
    filename: str

    @field_validator("format")
    @classmethod
    def checkFormat(cls,v):
        if v is None:
            raise ValueError("Format should be specified for template data files")
        return v

class LeafTemplateDataRaw(LeafTemplateData):
    data : Dict[str,str]

    @field_validator("format")
    @classmethod
    def checkFormat(cls,v):
        if v is not None:
            raise ValueError("Format should be None for raw template data")
        return v

class Template(BaseModel):
    filepath:str
    data: Optional[List[Union[LeafTemplateDataFile,LeafTemplateDataRaw]]] = []

class LeafMetadata(BaseModel):
    path: Optional[str] = None
    platform: Optional[str] = "local"
    templates:Optional[List[Template]] = []

class ComponentMap(BaseModel):
    component_order: List[str]
    mapping: Dict[str,Dict]

class Metadata(BaseModel):
    display_name: str
    description: Optional[str] = ""

class General(BaseModel):
    templates_directory: Optional[str] = None

class DashboardSchema(BaseModel):
    general : Optional[General] = None
    component_map: ComponentMap
    components: Dict[str,Dict[str, Metadata]]
    views : Dict[str,Dict]
    repositories : Dict[str,Metadata]