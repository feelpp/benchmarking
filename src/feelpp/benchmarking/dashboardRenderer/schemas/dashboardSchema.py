from pydantic import BaseModel
from typing import List, Dict, Optional, Union


class LeafTemplateData(BaseModel):
    filename: str
    prefix: Optional[str] = ""
    format: str
    action: Optional[str] = "input"

class LeafMetadata(BaseModel):
    path: Optional[str] = None
    platform: Optional[str] = "local"
    template_data:Optional[List[LeafTemplateData]] = []

class ComponentMap(BaseModel):
    component_order: List[str]
    mapping: Dict[str,Dict]

class Metadata(BaseModel):
    display_name: str
    description: Optional[str] = ""

class DashboardSchema(BaseModel):
    component_map: ComponentMap
    components: Dict[str,Dict[str, Metadata]]
    views : Dict[str,Dict]
    repositories : Dict[str,Metadata]