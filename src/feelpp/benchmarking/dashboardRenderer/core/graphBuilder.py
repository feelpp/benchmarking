from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import DashboardSchema, ComponentMap
from feelpp.benchmarking.dashboardRenderer.repository.registry import RepositoryRegistry
from feelpp.benchmarking.dashboardRenderer.repository.node import NodeComponentRepository
from feelpp.benchmarking.dashboardRenderer.views.base import ViewFactory, View
from feelpp.benchmarking.dashboardRenderer.repository.leaf import LeafComponentRepository
from feelpp.benchmarking.dashboardRenderer.repository.coordinator import RepositoryCoordinator
import os
import shutil

class ComponentGraphBuilder:
    def __init__(self, components_config:DashboardSchema, view:View) -> None:
        self.components_config = components_config.model_copy()
        self.view = view
        self.repositories = RepositoryRegistry()
        self.buildRepositories()

        self.coordinator = RepositoryCoordinator(self.repositories)
        self.coordinator.initRepositoryViews( self.components_config.views, self.components_config.component_map )

        self.coordinator.setLeavesParents()

    def buildRepositories(self):
        for repository_id, repository_template_info in self.components_config.repositories.items():
            self.repositories.addNodeRepository(
                NodeComponentRepository(
                    repository_id,
                    self.components_config.components[repository_id],
                    ViewFactory.create("node",repository_template_info,component_id=repository_id)
                )
            )

        self.repositories.setLeafRepository(
            LeafComponentRepository("leaves", self.components_config.component_map.mapping)
        )

    def render(self,base_dir:str, clean=False) -> None:
        pages_dir = os.path.join(base_dir,"pages")

        if clean and os.path.isdir(pages_dir):
            shutil.rmtree(pages_dir)

        self.view.render(pages_dir)

        for node_repository in self.repositories.node_repositories:
            node_repository.render(pages_dir)

        self.repositories.leaf_repository.render(pages_dir)

    def upstreamView(self):

        agg_children_data = {}

        for node_repository in self.repositories.node_repositories:
            node_repository.upstreamView()
            agg_children_data[node_repository.id] = node_repository.view.template_data

        self.view.updateTemplateData({"children": agg_children_data})

        # repository_results = [repo.view.template_data for repo in self.repositories.node_repositories]
        # self.view.updateTemplateData(dataCb(None,None,repository_results))
