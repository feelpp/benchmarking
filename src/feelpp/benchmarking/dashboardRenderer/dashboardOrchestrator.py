from feelpp.benchmarking.dashboardRenderer.controller import BaseControllerFactory, Controller
from feelpp.benchmarking.dashboardRenderer.repository import ComponentRepository
from feelpp.benchmarking.dashboardRenderer.utils import TreeUtils
from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import DashboardSchema, ComponentMap

import os

class DashboardOrchestrator:
    """ Serves as a repository orchestrator"""
    def __init__( self, components_config:DashboardSchema, title:str = "My Dashboard") -> None:
        self.home_page_controller:Controller = BaseControllerFactory.create("home")
        self.home_page_controller.updateData({"title":title})

        self.component_repositories:list[ComponentRepository] = [
            ComponentRepository(repository_id, components_config.components[repository_id], metadata = repository_metadata)
            for repository_id, repository_metadata in components_config.repositories.items()
        ]

        self.initRepositoryViews(components_config.views,components_config.component_map)


    def initRepositoryViews(self,views: dict[str,dict] ,component_map: ComponentMap) -> None:
        tree_order = component_map.component_order
        mapping = component_map.mapping
        for component_repository in self.component_repositories:
            component_views = views.get(component_repository.id,{})
            view_orders = TreeUtils.treeToLists({component_repository.id:component_views})
            for view_order in view_orders:
                view_perm = [tree_order.index(v) for v in view_order]
                permuted_tree = TreeUtils.permuteTreeLevels(mapping,view_perm)
                component_repository.initViews(view_order,permuted_tree,self.component_repositories)

    def getComponent(self,id:str) -> bool :
        for repo in self.component_repositories:
            if repo.has(id):
                return repo.get(id)
        return False

    def getRepository(self,id:str) -> ComponentRepository:
        return next(filter(lambda x: x.id ==id, self.component_repositories))

    def render(self,base_dir:str) -> None:
        pages_dir = os.path.join(base_dir)
        if not os.path.isdir(pages_dir):
            os.mkdir(pages_dir)
        self.home_page_controller.render(pages_dir)
        for component_repository in self.component_repositories:
            component_repository.render(base_dir = pages_dir)
