from feelpp.benchmarking.dashboardRenderer.core.treeBuilder import ComponentTree
from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import DashboardSchema
import json, os, shutil
from feelpp.benchmarking.dashboardRenderer.views.base import View, PreRenderPlugin
from typing import List, Type


class Dashboard:
    """
    Main orchestration class for the dashboard rendering process.
    It handles loading the configuration, initializing the ComponentTree structure, managing plugins, and executing the rendering steps.
    """
    def __init__( self, components_config_filepath:str, plugins:List[Type[PreRenderPlugin]] = [] ) -> None:
        """
        Args:
            components_config_filepath (str): The file path to the JSON configuration file defining the dashboard schema.
            plugins (List[Type['PreRenderPlugin']], optional): A list of plugin classes to be registered for processing template data. Defaults to [].
        """
        self.updatePlugins(plugins)
        components_config = self.loadConfig(components_config_filepath)

        self.tree = ComponentTree( components_config )

    def updatePlugins( self, plugins:List[Type[PreRenderPlugin]] ) -> None:
        """
        Extends the list of global plugins registered in the View base class.
        Plugins registered here will be applied to the template data of every View instance.
        Args:
            plugins (List[Type['PreRenderPlugin']]): A list of plugin classes to register.
        """
        View.plugins.extend(plugins)

    def loadConfig( self, filepath:str ) -> DashboardSchema:
        """
        Loads the JSON configuration file and validates it against the DashboardSchema.
        Args:
            filepath (str): The file path to the configuration JSON.
        Returns:
            DashboardSchema: The instantiated and validated schema object.
        Raises:
            FileNotFoundError: If the file does not exist.
            json.JSONDecodeError: If the file content is not valid JSON.
            pydantic.ValidationError: If the JSON structure does not match the DashboardSchema.
        """
        with open(filepath,"r") as f:
            components_config = DashboardSchema(**json.load(f))
        return components_config

    def print( self ) -> None:
        """ Prints the hierarchical structure of the component tree for debugging or review."""
        self.tree.print()

    def render( self, base_path:str, clean:bool = False ):
        """
        Triggers the rendering process, generating the final dashboard files.
        Args:
            base_path (str): The root directory where the final dashboard output will be placed.
            clean (bool, optional): If True, deletes the existing 'pages' directory before rendering. Defaults to False.
        """
        pages_dir = os.path.join( base_path, "pages" )

        if clean and os.path.isdir(pages_dir):
            shutil.rmtree(pages_dir)

        self.tree.render(pages_dir)

    def patchTemplateInfo( self, patches:List[str], targets:str, prefix:str, save:bool = False ):
        """
        Applies data patches to the TemplateInfo of specific leaf components.
        Args:
            patches (List[str]): List of patch file paths (JSON) to apply.
            targets (List[str]): List of component ID paths defining which leaves to patch.
            prefix (str): The prefix key under which the patch data should be stored.
            save (bool): If True, saves the modified TemplateInfo back to disk.
        """
        self.tree.patchTemplateInfo( patches, targets, prefix, save )
