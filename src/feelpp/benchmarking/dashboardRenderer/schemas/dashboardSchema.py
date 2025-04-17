from pydantic import BaseModel, field_validator, model_validator
from typing import List, Dict, Optional, Union


class TemplateDataFile(BaseModel):
    prefix: Optional[str] = ""
    format: str = None
    action: Optional[str] = "input"
    filepath: str

    @model_validator(mode="after")
    def checkFormat(self):
        if self.format is None:
            self.format = self.filepath.split(".")[-1]
        return self

class TemplateInfo(BaseModel):
    template:str = None
    data: Union[
        List[Union[TemplateDataFile,Dict[str,str]]],
        Union[TemplateDataFile,Dict[str,str]],
    ]

    @field_validator("data", mode="before")
    @classmethod
    def coerceData(cls, v):
        # Normalize to list
        if not isinstance(v, list):
            v = [v]
        # Try converting items with 'filepath' into TemplateDataFile
        result = []
        for item in v:
            if isinstance(item, dict) and "filepath" in item:
                result.append(TemplateDataFile(**item))
            else:
                result.append(item)
        return result


class LeafMetadata(BaseModel):
    path: Optional[str] = None
    platform: Optional[str] = "local"
    template_info:Optional[Union[Dict[str,str],TemplateInfo]] = TemplateInfo(data = {})


class ComponentMap(BaseModel):
    component_order: List[str]
    mapping: Dict[str,Dict]


class DashboardSchema(BaseModel):
    dashboard_metadata:Optional[Union[dict[str,str],TemplateInfo]] = TemplateInfo(data={})
    component_map: ComponentMap
    components: Dict[str,Dict[str, Union[dict[str,str],TemplateInfo]]]
    views : Dict[str,Dict]
    repositories : Dict[str,Union[dict[str,str],TemplateInfo]]

    @staticmethod
    def castTemplateInfo(v):
        for node, template_info in v.items():
            if not isinstance(template_info,TemplateInfo):
                v[node] = TemplateInfo(data=template_info)
        return v


    @field_validator("dashboard_metadata",mode="after")
    @classmethod
    def castDashboardMeta(cls,v):
        if not isinstance(v,TemplateInfo):
            return TemplateInfo(data=v)
        return v

    @field_validator("repositories",mode="after")
    @classmethod
    def castRepoTemplateInfo(cls,v):
        return cls.castTemplateInfo(v)

    @field_validator("components",mode="after")
    @classmethod
    def castNodeTemplateInfo(cls,v):
        for repo, nodes in v.items():
            v[repo] = cls.castTemplateInfo(nodes)
        return v

