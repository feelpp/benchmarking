from pydantic import BaseModel, field_validator, model_validator
from typing import List, Dict, Optional, Union


def castTemplateInfo(v):
    for node, template_info in v.items():
        if not isinstance(template_info,TemplateInfo):
            v[node] = TemplateInfo(data=template_info)
    return v


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
    template:Optional[str] = None
    data: Union[
        List[Union[TemplateDataFile,Dict]],
        Union[TemplateDataFile,Dict],
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
    template_info:Optional[Union[Dict,TemplateInfo]] = TemplateInfo(data = {})


    @field_validator("template_info",mode="after")
    @classmethod
    def castNodeTemplateInfo(cls,v):
        if not isinstance(v,TemplateInfo):
            return TemplateInfo(data=v.get("data",[]),template=v.get("template",""))
        return v


class ComponentMap(BaseModel):
    component_order: Optional[List[str]] = None
    mapping: Dict[str,Dict]

class TemplateDefaults(BaseModel):
    repositories: Optional[Union[Dict,TemplateInfo]] = TemplateInfo(data = {})
    components: Optional[Union[Dict[str,Union[Dict,TemplateInfo]], TemplateInfo]] = {}
    leaves: Optional[Union[Dict,TemplateInfo]] = TemplateInfo(data = {})


    @field_validator("repositories","leaves",mode="after")
    @classmethod
    def castRepoTemplateInfo(cls,v):
        if not isinstance(v,TemplateInfo):
            if "data" in v:
                v = TemplateInfo(data=v.get("data",[]), template = v.get("template",None))
            else:
                v = TemplateInfo(data = v)
            return v

    @field_validator("components",mode="after")
    @classmethod
    def castNodeTemplateInfo(cls,v):
        for node, template_info in v.items():
            if not isinstance(v,TemplateInfo):
                if "data" in template_info:
                    v[node] = TemplateInfo(data=template_info.get("data",[]), template = template_info.get("template",None))
                else:
                    v[node] = TemplateInfo(data = template_info)
        return v


class DashboardSchema(BaseModel):
    dashboard_metadata:Optional[Union[dict[str,str],TemplateInfo]] = TemplateInfo(data={})
    component_map: Union[ComponentMap,Dict]
    components: Dict[str,Dict[str, Union[dict[str,str],TemplateInfo]]]
    views : Optional[Dict[str,Union[Dict,str]]] = None
    repositories : Optional[Dict[str,Union[dict[str,str],TemplateInfo]]] = None
    template_defaults: Optional[TemplateDefaults] = TemplateDefaults()

    @model_validator(mode="after")
    def inferRepositories(self):
        if self.repositories is None:
            self.repositories = {}
            for repo_name in self.components:
                self.repositories[repo_name] = TemplateInfo(data={"title":repo_name.title()})
        return self

    @field_validator("component_map",mode="after")
    @classmethod
    def coerceComponentMap(cls,v):
        if isinstance(v,dict) and "mapping" not in v:
            v = ComponentMap(mapping=v)
        return v

    @model_validator(mode="after")
    def inferOrder(self):
        if self.component_map.component_order is not None:
            return self

        mapping = self.component_map.mapping
        order = []
        def find_order_level(d, level=0):
            if not isinstance(d, dict) or not d:
                return
            for key in d.keys():
                # Find the first matching component key at this level
                for comp_name in self.components.keys():
                    if key in d and comp_name not in order:
                        order.append(comp_name)
                # Recurse into the first child for deeper levels
                first_child = next(iter(d.values()))
                find_order_level(first_child, level + 1)
                break  # only need first branch

        find_order_level(mapping)
        self.component_map.component_order = order
        return self

    @model_validator(mode="after")
    def setDefaultViews(self):
        if self.views is None:
            current_views = {}
            self.views = current_views
            current_views = self.component_map.component_order[-1]
            for key in reversed(self.component_map.component_order[:-1]):
                current_views = {key: current_views}
            self.views = current_views
        return self


    @field_validator("dashboard_metadata",mode="after")
    @classmethod
    def castDashboardMeta(cls,v):
        if not isinstance(v,TemplateInfo):
            return TemplateInfo(data=v)
        return v

    @field_validator("repositories",mode="after")
    @classmethod
    def castRepoTemplateInfo(cls,v):
        return castTemplateInfo(v)

    @field_validator("components",mode="after")
    @classmethod
    def castNodeTemplateInfo(cls,v):
        for repo, nodes in v.items():
            v[repo] = castTemplateInfo(nodes)
        return v

    @model_validator(mode="after")
    def setTemplateDefaults(self):

        #Validate that all components keys are existing repositories
        for k in self.template_defaults.components:
            if k not in ["all"] + list(self.repositories.keys()):
                raise ValueError(f"Template defaults: {k} does not exist in repositories")

        for repo, repo_data in self.repositories.items():
            if not repo_data.template:
                repo_data.template = self.template_defaults.repositories.template
            repo_data.data += self.template_defaults.repositories.data

        for component_repo, components in self.components.items():
            for component_id, component_data in components.items():
                template = None
                if "all" in self.template_defaults.components:
                    template = self.template_defaults.components["all"].template
                    component_data.data += self.template_defaults.components["all"].data

                if component_repo in self.template_defaults.components:
                    template = self.template_defaults.components[component_repo].template or template
                    component_data.data += self.template_defaults.components[component_repo].data
                if not component_data.template:
                    component_data.template = template

        return self
