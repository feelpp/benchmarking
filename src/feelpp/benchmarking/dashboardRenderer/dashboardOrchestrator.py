from feelpp.benchmarking.dashboardRenderer.controller import BaseControllerFactory, Controller
from feelpp.benchmarking.dashboardRenderer.repository import NodeComponentRepository, LeafComponentRepository
from feelpp.benchmarking.dashboardRenderer.utils import TreeUtils
from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import DashboardSchema, ComponentMap

import os

class DashboardOrchestrator:
    """ Serves as a repository orchestrator"""
    def __init__( self, components_config:DashboardSchema, title:str = "My Dashboard") -> None:
        self.home_page_controller:Controller = BaseControllerFactory.create("home")
        self.home_page_controller.updateData({"title":title})

        self.components_config = components_config.model_copy()

        self.component_repositories:list[NodeComponentRepository] = [
            NodeComponentRepository(repository_id, self.components_config.components[repository_id], metadata = repository_metadata)
            for repository_id, repository_metadata in self.components_config.repositories.items()
        ]

        self.leaf_component_repository:LeafComponentRepository = LeafComponentRepository("leaves", self.components_config.component_map.mapping,self.component_repositories)

        self.initRepositoryViews(self.components_config.views,self.components_config.component_map)


    def initRepositoryViews(self,views: dict[str,dict] ,component_map: ComponentMap) -> None:
        tree_order = component_map.component_order
        mapping = component_map.mapping
        for component_repository in self.component_repositories:
            component_views = views.get(component_repository.id,{})
            view_orders = TreeUtils.treeToLists({component_repository.id:component_views})
            for view_order in view_orders:
                view_perm = [tree_order.index(v) for v in view_order] + [len(view_order)]
                permuted_tree = TreeUtils.permuteTreeLevels(mapping,view_perm)
                component_repository.initViews(view_order,permuted_tree,self.component_repositories,self.leaf_component_repository)

    def getComponent(self,id:str) -> bool :
        for repo in self.component_repositories:
            if repo.has(id):
                return repo.get(id)
        return False

    def getRepository(self,id:str) -> NodeComponentRepository:
        return next(filter(lambda x: x.id ==id, self.component_repositories))

    def render(self,base_dir:str) -> None:
        pages_dir = os.path.join(base_dir,"pages")
        if not os.path.isdir(pages_dir):
            os.mkdir(pages_dir)

        self.home_page_controller.render(pages_dir)


        for view in self.components_config.views:
            self.getRepository(view).render(base_dir = pages_dir)

        self.leaf_component_repository.render(pages_dir)