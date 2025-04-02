from feelpp.benchmarking.dashboardRenderer.controller import BaseControllerFactory, Controller
from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import Metadata, Template
import os, json
from itertools import permutations

class Component:
    def __repr__(self):
        return f"<{self.id}>"

class NodeComponent(Component):
    def __init__(self, id:str, metadata: Metadata, parent_repository_id:str, custom_templates_dir:str = None ) -> None:
        self.id = id
        self.initBaseController(metadata,custom_templates_dir)
        self.parent_repository_id = parent_repository_id
        self.metadata = metadata
        self.views = {}

    def initBaseController(self,metadata:Metadata, custom_templates_dir:str = None ):

        self.index_page_controller:Controller = BaseControllerFactory.create("index",custom_templates_dir)
        self.index_page_controller.updateData(dict(
            title = metadata.display_name,
            description = metadata.description,
            card_image = f"ROOT:{self.id}.jpg"
        ))


    def updateViewsWithLeaves(self,leaves, views = None,  path=[]):
        views = self.views if views is None else views

        if not isinstance(views,dict):
            return

        if views == {}:
            curr = self.views
            for key in path[:-1]:
                curr = curr.setdefault(key,{})
            curr[path[-1]] = list(leaves)
        else:
            for repo_id, component_views in views.items():
                for component, children_views in component_views.items():
                    self.updateViewsWithLeaves(
                        leaves = filter(lambda x : component in x.parents, leaves),
                        views = children_views,
                        path = path + [repo_id,component]
                    )


    def render(self,base_dir:str, parent, parent_id, views = None ) -> None:
        views = self.views if views is None else views

        component_dir = os.path.join(base_dir,self.id)
        if not os.path.isdir(component_dir):
            os.mkdir(component_dir)

        self.index_page_controller.render(
            component_dir,
            parent_ids = parent_id,
            breadcrumbs = parent.metadata.display_name + " > " + self.metadata.display_name,
            self_id = f"{parent_id}-{self.id}"
        )

        if not isinstance(views,dict):
            return
        for _, children_views in views.items():
            for children_component,children_view in children_views.items():
                children_component.render(
                    component_dir,
                    parent = self,
                    parent_id = f"{parent_id}-{self.id}",
                    views = children_view
                )

class LeafComponent(Component):
    def __init__(self, id:str , data_path: str, templates:list[Template], parents: list[str], custom_templates_dir:str = None ):
        self.id = id
        self.parents = parents

        self.initBaseController(custom_templates_dir)
        for template in templates:
            for data in template.data:
                if data.action == "input":
                    if not data.format:
                        self.leaf_page_controller.updateData({data.prefix:data.data} if data.prefix else data.data)
                    else:
                        with open(os.path.join(data_path,data.filename),"r") as f:
                            if data.format == "json":
                                data_dict = json.load(f)
                                self.leaf_page_controller.updateData({data.prefix:data_dict} if data.prefix else data_dict)
                            else:
                                raise NotImplementedError(f"Format {data.format} is supported")
                else:
                    raise NotImplementedError(f"Action {data.action} is supported")
        self.leaf_page_controller.updateData(dict(plugin_templates=[t.filepath for t in templates]))


    def initBaseController(self, custom_templates_dir:str = None ):
        self.leaf_page_controller:Controller = BaseControllerFactory.create("leaf",custom_templates_dir)
        self.leaf_page_controller.updateData(dict(
            title = self.id
        ))

    def buildFilename(self):
        extension = self.leaf_page_controller.output_filename.split(".")[-1]
        return f"{'-'.join([p.id for p in self.parents])}-{self.id}.{extension}"

    def render(self,base_dir):
        perms = permutations(self.parents)
        self.leaf_page_controller.output_filename = self.buildFilename()
        self.leaf_page_controller.render(
            base_dir,
            parent_ids = ",".join([ f"{perm[0].parent_repository_id}-{'-'.join([p.id for p in perm])}" for perm in perms ])
        )