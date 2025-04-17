from feelpp.benchmarking.dashboardRenderer.core.graphBuilder import ComponentGraphBuilder
from feelpp.benchmarking.dashboardRenderer.views.base import ViewFactory
from schemas.dashboardSchema import DashboardSchema, TemplateInfo
import json

class Dashboard:
    def __init__(self,components_config_filepath:str, template_data:dict = {}):
        components_config = self.loadConfig(components_config_filepath)
        self.builder = ComponentGraphBuilder(
            components_config,
            ViewFactory.create("home",TemplateInfo(data=template_data))
        )

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