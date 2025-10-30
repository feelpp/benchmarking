from feelpp.benchmarking.dashboardRenderer.core.graphBuilder import ComponentGraphBuilder
from feelpp.benchmarking.dashboardRenderer.views.base import ViewFactory
from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import DashboardSchema
import json
from feelpp.benchmarking.dashboardRenderer.views.base import View


class Dashboard:
    def __init__(self,components_config_filepath:str, plugins:dict = {}):
        self.updatePlugins(plugins)
        components_config = self.loadConfig(components_config_filepath)
        self.builder = ComponentGraphBuilder(
            components_config,
            ViewFactory.create("home",components_config.dashboard_metadata)
        )

    def updatePlugins(self,plugins):
        View.plugins.update(plugins)

    def loadConfig(self,filepath):
        with open(filepath,"r") as f:
            components_config = DashboardSchema(**json.load(f))
        return components_config

    def render(self,base_path,clean=False):
        self.builder.render(base_path,clean)

    def printViews(self,repository=None,component=None):
        item = self.builder.repositories
        if repository and component:
            print(repository)
            print("\t",component)
            item = item.getRepository(repository).get(component)
        elif repository:
            print(repository)
            item = item.getRepository(repository)
        elif component:
            print(component)
            item = item.getComponent(component)
        item.printViews()

    def patchTemplateInfo(self,patches:list[str],targets:str,prefix:str,save:bool):
        self.builder.coordinator.patchTemplateInfo(patches,targets,prefix,save)

    def upstreamView(self,
                     dataCb = lambda component,component_data : component_data,
                     leafCb = lambda leaves : [leaf.view.template_data for leaf in leaves] ):
        self.builder.upstreamView(dataCb,leafCb)