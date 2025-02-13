from feelpp.benchmarking.dashboardRenderer.renderer import TemplateRenderer
from feelpp.benchmarking.dashboardRenderer.repository import ComponentRepository
from feelpp.benchmarking.dashboardRenderer.utils import TreeUtils

import os

class DashboardOrchestrator:
    """ Serves as a repository orchestrator"""
    def __init__(self,components_config):

        self.component_repositories = [
            ComponentRepository(repository_id, components)
            for repository_id, components in components_config.components.items()
        ]

        self.initRepositoryViews(components_config.views,components_config.component_map)

    def initRepositoryViews(self,views,component_map):
        tree_order = component_map.component_order
        mapping = component_map.mapping
        for component_repository in self.component_repositories:
            component_views = views.get(component_repository.id,{})
            view_orders = TreeUtils.treeToLists({component_repository.id:component_views})
            for view_order in view_orders:
                view_perm = [tree_order.index(v) for v in view_order]
                permuted_tree = TreeUtils.permuteTreeLevels(mapping,view_perm)
                component_repository.initViews(view_order,permuted_tree,self.component_repositories)

    def getComponent(self,id):
        for repo in self.component_repositories:
            if repo.has(id):
                return repo.get(id)
        return False

    def getRepository(self,id):
        return next(filter(lambda x: x.id ==id, self.component_repositories))