from pydantic import BaseModel, field_validator, model_validator
from typing import List, Dict, Optional, Union
import os
from importlib.resources import files


def _items_equal(a, b):
    """
    Deep-equality check for TemplateDataFile, dict, or simple types.
    """
    if isinstance(a, BaseModel) and isinstance(b, BaseModel):
        return a.model_dump() == b.model_dump()

    if isinstance(a, dict) and isinstance(b, dict):
        return a == b

    return a == b

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

    @field_validator("template",mode="after")
    @classmethod
    def expandTemplate(cls, v:str):
        if v is None:
            return v

        template_dir_env = os.getenv("TEMPLATE_DIR")
        if template_dir_env and os.path.isdir(template_dir_env):
            template_dir = os.path.abspath(template_dir_env)
        else:
            template_dir = os.path.join(files("feelpp.benchmarking.report"),"templates")
            if not os.path.isdir(template_dir):
                template_dir = "./src/feelpp/benchmarking/report/templates/"

        return v.replace("${TEMPLATE_DIR}",template_dir)

    def merge(self, other: "TemplateInfo"):
        if other.template:
            self.template = other.template

        for item in other.data:
            if not any(_items_equal(item, existing) for existing in self.data):
                self.data.append(item)

        return self


class LeafMetadata(BaseModel):
    path: Optional[str] = None
    platform: Optional[str] = "local"
    template_info:Optional[Union[Dict,TemplateInfo]] = TemplateInfo(data = {})


    @field_validator("template_info",mode="after")
    @classmethod
    def castNodeTemplateInfo(cls,v):
        if not isinstance(v,TemplateInfo):
            if "data" in v or "template" in v:
                v = TemplateInfo(data=v.get("data",[]), template = v.get("template",None))
            else:
                v = TemplateInfo(data = v)
        return v

    def merge(self, other: "LeafMetadata"):
        if other.path:
            self.path = other.path
        if other.platform:
            self.platform = other.platform
        self.template_info.merge(other.template_info)
        return self

class ComponentMap(BaseModel):
    component_order: Optional[List[str]] = None
    mapping: Dict[str,Dict]


    def merge(self, other: "ComponentMap"):
        def merge_mapping(a, b):
            for key, val in b.items():
                if key not in a:
                    a[key] = val
                else:
                    if isinstance(a[key], dict) and isinstance(val, dict):
                        merge_mapping(a[key], val)
                    else:
                        a[key] = val
            return a

        self.mapping = merge_mapping(self.mapping, other.mapping)

        # component_order: replace if other provides it
        if other.component_order:
            self.component_order = other.component_order

        return self

class TemplateDefaults(BaseModel):
    repositories: Optional[Union[Dict,TemplateInfo]] = TemplateInfo(data = {})
    components: Optional[Union[Dict[str,Union[Dict,TemplateInfo]], TemplateInfo]] = {}
    leaves: Optional[Union[Dict,TemplateInfo]] = TemplateInfo(data = {})


    @field_validator("repositories","leaves",mode="after")
    @classmethod
    def castRepoTemplateInfo(cls,v):
        if not isinstance(v,TemplateInfo):
            if "data" in v or "template" in v:
                v = TemplateInfo(data=v.get("data",[]), template = v.get("template",None))
            else:
                v = TemplateInfo(data = v)
        return v

    @field_validator("components",mode="after")
    @classmethod
    def castNodeTemplateInfo(cls,v):
        for node, template_info in v.items():
            if not isinstance(v,TemplateInfo):
                if "data" in template_info or "template" in template_info:
                    v[node] = TemplateInfo(data=template_info.get("data",[]), template = template_info.get("template",None))
                else:
                    v[node] = TemplateInfo(data = template_info)
        return v

    def merge(self, other: "TemplateDefaults"):
        self.repositories.merge(other.repositories)
        self.leaves.merge(other.leaves)

        for k, v in other.components.items():
            if k in self.components:
                self.components[k].merge(v)
            else:
                self.components[k] = v

        return self


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
        def findOrder(d):
            if not isinstance(d, dict) or not d:
                return
            for key, value in d.items():
                for repo_type, components in self.components.items():
                    if key in components and repo_type not in order:
                        order.append(repo_type)
                findOrder(value)


        findOrder(mapping)
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

    @staticmethod
    def _extend_unique(target_list, new_items):
        for item in new_items:
            if not any(_items_equal(item, existing) for existing in target_list):
                target_list.append(item)

    @model_validator(mode="after")
    def setTemplateDefaults(self):

        #Validate that all components keys are existing repositories
        for k in self.template_defaults.components:
            if k not in ["all"] + list(self.repositories.keys()):
                raise ValueError(f"Template defaults: {k} does not exist in repositories")

        for repo, repo_data in self.repositories.items():
            if not repo_data.template:
                repo_data.template = self.template_defaults.repositories.template
            self._extend_unique(repo_data.data, self.template_defaults.repositories.data)

        for component_repo, components in self.components.items():
            for component_id, component_data in components.items():
                template = None
                if "all" in self.template_defaults.components:
                    template = self.template_defaults.components["all"].template
                    self._extend_unique(component_data.data, self.template_defaults.components["all"].data)

                if component_repo in self.template_defaults.components:
                    template = self.template_defaults.components[component_repo].template or template
                    self._extend_unique(component_data.data,self.template_defaults.components[component_repo].data)

                if not component_data.template:
                    component_data.template = template

        return self

    def merge(self, other: "DashboardSchema"):
        def deep_merge(a, b):
            """
            Merge b into a.
            - If both values are dicts → recursive merge.
            - If both are TemplateInfo → call TemplateInfo.merge().
            - Otherwise → replace.
            """
            if isinstance(a, TemplateInfo) and isinstance(b, TemplateInfo):
                return a.merge(b)

            if isinstance(a, dict) and isinstance(b, dict):
                for key, b_val in b.items():
                    if key not in a:
                        a[key] = b_val
                    else:
                        a[key] = deep_merge(a[key], b_val)
                return a

            return b

        # dashboard_metadata
        if other.dashboard_metadata:
            self.dashboard_metadata = deep_merge( self.dashboard_metadata,other.dashboard_metadata)

        # repositories
        if other.repositories:
            if self.repositories is None:
                self.repositories = other.repositories
            else:
                self.repositories = deep_merge(self.repositories, other.repositories)

        # components
        if other.components:
            for repo, comp_dict in other.components.items():
                if repo not in self.components:
                    self.components[repo] = comp_dict
                else:
                    self.components[repo] = deep_merge( self.components[repo], comp_dict )

        # component_map
        if other.component_map:
            self.component_map.merge(other.component_map)

        # views
        if other.views:
            if self.views is None:
                self.views = other.views
            else:
                self.views = deep_merge(self.views, other.views)

        # template_defaults
        if other.template_defaults:
            self.template_defaults.merge(other.template_defaults)

        return self
