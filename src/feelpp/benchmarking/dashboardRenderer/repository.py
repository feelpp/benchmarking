import os
from feelpp.benchmarking.dashboardRenderer.component import Component
from feelpp.benchmarking.dashboardRenderer.utils import TreeUtils
from feelpp.benchmarking.dashboardRenderer.controller import BaseControllerFactory, Controller
from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import Metadata

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

class ComponentRepository(Repository):
    """Class representing a collection of components"""
    def __init__( self, id:str, components:dict[str,dict], metadata: Metadata ):
        super().__init__(id)
        self.data: list[Component]

        self.initBaseController(metadata)

        for component_id, component_metadata in components.items():
            self.add(Component(component_id, component_metadata, self.id))

    def initBaseController(self,metadata:Metadata):
        self.index_page_controller:Controller = BaseControllerFactory.create("index")
        self.index_page_controller.updateData(dict(
            title = metadata.display_name,
            self_id = self.id,
            parent_ids = "dashboard-index",
            description = metadata.description,
            card_image = ""
        ))

    def initViews(self, view_order, tree, other_repositories):
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

    def render(self,base_dir:str) -> None:
        repository_dir = os.path.join(base_dir,self.id)
        if not os.path.isdir(repository_dir):
            os.mkdir(repository_dir)

        self.index_page_controller.render(repository_dir)
        for component in self.data:
            component.render(base_dir = repository_dir)
            pass


    # def renderSelf(self, base_dir, renderer, self_tag_id, parent_id = "catalog-index"):
    #     """ Initialize the module for repository.
    #     Creates the directory for the repository and renders the index.adoc file
    #     Args:
    #         base_dir (str): The base directory for the modules
    #         renderer (Renderer): The renderer to use
    #         self_tag_id (str): The catalog id of the current reposirory, to be used by their children as parent
    #         parent_id (str): The catalog id of the parent component
    #     """
    #     module_path = os.path.join(base_dir, self.id)

    #     if not os.path.exists(module_path):
    #         os.mkdir(module_path)

    #     renderer.render(
    #         os.path.join(module_path,"index.adoc"),
    #         self.indexData(parent_id,self_tag_id)
    #     )

    # def renderChildren(self, base_dir, renderer):
    #     """ Inits the repository module and calls the initModules method of each item in the repository.
    #     Args:
    #         base_dir (str): The base directory for the modules
    #         renderer (Renderer): The renderer to use
    #         parent_id (str,optional): The catalog id of the parent component. Defaults to "supercomputers".
    #     """
    #     for item in self.data:
    #         item.render(os.path.join(base_dir,self.id), renderer, self.id)

    # def render(self, base_dir, renderer, parent_id = "catalog-index"):
    #     """ Inits the repository module and calls the initModules method of each item in the repository.
    #     Args:
    #         base_dir (str): The base directory for the modules
    #         renderer (Renderer): The renderer to use
    #         parent_id (str,optional): The catalog id of the parent component. Defaults to "supercomputers".
    #     """
    #     self.renderSelf(base_dir,renderer,self_tag_id=self.id, parent_id=parent_id)
    #     self.renderChildren(base_dir, renderer)
