from feelpp.benchmarking.dashboardRenderer.core.treeBuilder import ComponentTree
from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import DashboardSchema
import json, os, shutil
from feelpp.benchmarking.dashboardRenderer.views.base import View


class Dashboard:
    def __init__(self,components_config_filepath:str, plugins:list = []):
        self.updatePlugins(plugins)
        components_config = self.loadConfig(components_config_filepath)

        self.tree = ComponentTree( components_config )

    def updatePlugins(self,plugins):
        View.plugins.extend(plugins)

    def loadConfig(self,filepath):
        with open(filepath,"r") as f:
            components_config = DashboardSchema(**json.load(f))
        return components_config

    def print(self):
        self.tree.print()

    def render(self,base_path,clean=False):
        pages_dir = os.path.join(base_path,"pages")

        if clean and os.path.isdir(pages_dir):
            shutil.rmtree(pages_dir)

        self.tree.render(pages_dir)

    def patchTemplateInfo(self,patches:list[str],targets:str,prefix:str,save:bool):
        self.tree.patchTemplateInfo(patches,targets,prefix,save)
