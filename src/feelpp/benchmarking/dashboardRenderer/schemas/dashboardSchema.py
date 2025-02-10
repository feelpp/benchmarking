from pydantic import BaseModel
from typing import List, Dict, Optional

class ComponentMap(BaseModel):
    component_order: List[str]
    mapping: Dict[str,Dict]

class ComponentMetadata(BaseModel):
    display_name: str
    description: Optional[str] = ""

class DashboardSchema(BaseModel):
    component_map: ComponentMap
    components: Dict[str,Dict[str, ComponentMetadata]]
    views : Dict[str,Dict]