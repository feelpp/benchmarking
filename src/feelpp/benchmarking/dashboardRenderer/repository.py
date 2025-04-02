import os
from feelpp.benchmarking.dashboardRenderer.component import NodeComponent, LeafComponent
from feelpp.benchmarking.dashboardRenderer.utils import TreeUtils
from feelpp.benchmarking.dashboardRenderer.controller import BaseControllerFactory, Controller
from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import Metadata, ComponentMap, LeafMetadata

class Repository:
    """ Base class for repositories.
    Designed for containing and manipulating a unique list of items
    """
    def __init__(self,id):
        self.data = []
        self.id = id

    def __iter__(self):
        """ Iterator for the repository """
        return iter(self.data)

    def __repr__(self):
        return f"< {self.id} : [{', '.join([str(d) for d in self.data])}] >"

    def add(self, item):
        """ Add an item to the repository, ensuring it is unique
        Args:
            item (object): The item to add
        """
        if item not in self.data and item.id not in [x.id for x in self.data]:
            self.data.append(item)

    def get(self, id):
        """ Get an item by its id """
        return next(filter(lambda x: x.id == id, self.data))

    def has(self, id):
        """ Return true if the component with id exists in data """
        return id in [x.id for x in self.data]

    def __getitem__(self,index):
        """ [] overload returning the item in data in position 'index' """
        return self.data[index]

    def __len__(self):
        return len(self.data)

class NodeComponentRepository(Repository):
    """Class representing a collection of components"""
    def __init__( self, id:str, components:dict[str,dict], metadata: Metadata, custom_templates_dir:str = None ):
        super().__init__(id)
        self.data: list[NodeComponent]
        self.metadata = metadata

        self.initBaseController(metadata)

        for component_id, component_metadata in components.items():
            self.add(NodeComponent(component_id, component_metadata,self.id, custom_templates_dir))

    def initBaseController(self,metadata:Metadata):
        self.index_page_controller:Controller = BaseControllerFactory.create("index")
        self.index_page_controller.updateData(dict(
            title = metadata.display_name,
            self_id = self.id,
            parent_ids = "dashboard_index",
            description = metadata.description,
            card_image = f"ROOT:{self.id}.jpg"
        ))

    def initViews(self, view_order, tree, other_repositories, leaf_repository):
        repo_lookup = {rep.id: rep for rep in other_repositories}

        def processViewTree(subtree, level_index, unwrap_first=False):
            if level_index >= len(view_order) or not subtree:
                return {}

            current_repo = repo_lookup[view_order[level_index]]
            grouped_subtree = {}
            for view_component_id, sub_tree in subtree.items():
                grouped_subtree.setdefault(view_order[level_index], {})[view_component_id] = sub_tree

            result = {}
            for component_type, components in grouped_subtree.items():
                level_result = {
                    current_repo.get(comp_id): processViewTree(sub_tree, level_index + 1)
                    for comp_id, sub_tree in components.items()
                }
                if unwrap_first:
                    result.update(level_result)
                else:
                    result.update({component_type:level_result})
            return result

        for component in self.data:
            component_subtree = tree.get(component.id, {})
            component.views = TreeUtils.mergeDicts(component.views,{view_order[1]:processViewTree(component_subtree, 1, unwrap_first=True)})
            component.updateViewsWithLeaves(leaf_repository)

    def render(self,base_dir:str) -> None:
        repository_dir = os.path.join(base_dir,self.id)

        if not os.path.isdir(repository_dir):
            os.mkdir(repository_dir)

        self.index_page_controller.render(repository_dir)

        for component in self.data:
            component.render(base_dir = repository_dir, parent= self, parent_id=self.id)


class LeafComponentRepository(Repository):
    def __init__(self, id, component_mapping:ComponentMap,other_repositories:list[Repository], custom_templates_dir:str = None ):
        super().__init__(id)
        self.data: list[LeafComponent]
        self.custom_templates_dir = custom_templates_dir
        self.initLeaves(other_repositories,component_mapping)

    def initLeaves(self,other_repositories:list[Repository], d, path=[]):

        if not isinstance(d, dict):
            return

        if any(not isinstance(v, dict) for v in d.values()):
            self.addLeaves(LeafMetadata(**d),path,other_repositories)
        else:
            for key, value in d.items():
                self.initLeaves(other_repositories,value, path + [key])

    def getParentComponent(self,id, other_repositories:list[Repository]):
        for repo in other_repositories:
            if repo.has(id):
                return repo.get(id)


    def addLeaves(self,leaf_config: LeafMetadata, parent_path:list[str], other_repositories:list[Repository]):
        if leaf_config.path is None:
            return

        if leaf_config.platform != "local":
            #Download files and then pass location
            raise NotImplementedError("Remote locations not yet implemented")

        if not os.path.exists(leaf_config.path):
            raise FileNotFoundError(f"{leaf_config.path} does not contain any files")

        for leaf_component_dir in os.listdir(leaf_config.path):
            self.add(LeafComponent(
                f"{leaf_component_dir}",
                os.path.join(leaf_config.path,leaf_component_dir),
                leaf_config.templates,
                [self.getParentComponent(parent_id,other_repositories) for parent_id in parent_path],
                self.custom_templates_dir
            ))

    def render(self,base_dir:str) -> None:
        leaves_dir = os.path.join(base_dir,self.id)
        if not os.path.isdir(leaves_dir):
            os.mkdir(leaves_dir)

        for component in self.data:
            component.render( base_dir = leaves_dir )

