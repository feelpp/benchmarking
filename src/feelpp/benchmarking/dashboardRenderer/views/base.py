from typing import Union, Dict, Any, Optional, Type, List
from datetime import datetime
import os, shutil
from copy import deepcopy
from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import TemplateInfo,TemplateDataFile
from feelpp.benchmarking.dashboardRenderer.renderer import BaseRendererFactory, TemplateRenderer
from feelpp.benchmarking.dashboardRenderer.views.templateDataHandler import TemplateDataHandlerFactory

class View:
    """
    Encapsulates all components required to render a single output file (e.g., an AsciiDoc page).

    A View manages the Jinja2 Renderer, template configuration, input data, and asset files (partials).
    It is the core abstraction for transforming structured data into a rendered document.
    """

    plugins:List[Type["PreRenderPlugin"]] = []

    def __init__(
            self,
            base_template_type:str,
            template_info:TemplateInfo,
            template_data_dir:str = None,
            base_template_data:Dict[str,Any] = {},
            out_filename:str = None
        ) -> None:
        """
        Args:
            base_template_type (str): The general type of the component ("home", "node", or "leaf").
            template_info (TemplateInfo): Schema object holding template configuration (e.g., extra data files).
            template_data_dir (Optional[str], optional): Base directory for resolving relative paths in data files. Defaults to None.
            base_template_data (Dict[str, Any], optional): Initial, hardcoded data to be included in the context. Defaults to {}.
            out_filename (Optional[str], optional): The suggested filename for the rendered output. Defaults to None.
        """
        self.partials = {}
        self.extra_renderers = {}
        self.renderer = self.initRenderer( base_template_type, template_info.template )


        self.template_data = {}
        self.updateTemplateData( base_template_data )

        self.out_filename = out_filename
        self.template_info = template_info
        self.template_data_dir = template_data_dir


        if template_info.template:
            self.addExtraTemplate( template_info.template )

        for data in template_info.data:
            self.updateTemplateData( data, template_data_dir )

    def clone( self ):
        """
        Creates a shallow copy of the View, but ensures deep copying of mutable data (`template_data`).
        The underlying `renderer` and other configuration attributes are copied by reference.
        Returns:
            View: A new View instance with identical, but independent, data context.
        """
        cloned_view = self.__class__.__new__( self.__class__ )

        cloned_view.renderer = self.renderer
        cloned_view.template_info = self.template_info
        cloned_view.template_data_dir = self.template_data_dir
        cloned_view.out_filename = self.out_filename
        cloned_view.partials = self.partials.copy()
        cloned_view.extra_renderers = self.extra_renderers.copy()

        cloned_view.template_data = deepcopy( self.template_data )

        return cloned_view

    def initRenderer( self, base_template_type:str, template:Optional[str] = None ) -> TemplateRenderer:
        """
        Initializes the concrete `TemplateRenderer` instance using the `BaseRendererFactory`.

        Args:
            base_template_type (str): The key defining the base template to use ("home", "node", or "leaf").
            template (Optional[str], optional): Path to a custom template file. Its directory is used as an extra lookup path for the renderer. Defaults to None.
        Returns:
            TemplateRenderer: An initialized template renderer.
        """
        renderer = BaseRendererFactory.create(
            base_template_type,
            os.path.dirname(template) if template else None
        )
        return renderer

    def addExtraTemplate( self, template:str ) -> None:
        """
        Adds a template file name to the `extra_templates` list in the template data.
        This allows the primary template to reference and include the content of a custom template.

        Args:
            template (str): The path to the custom template file. Only the basename is stored.
        """
        if "extra_templates" not in self.template_data:
            self.template_data["extra_templates"] = []
        self.template_data["extra_templates"].append( os.path.basename(template) )

    def updateTemplateData( self, data:Union[TemplateDataFile,Dict[str,Any]], template_data_dir:str = None ) -> None:
        """
        Uses the `TemplateDataHandlerFactory` to process the input data and merge the result into the view's template data context.

        Args:
            data (Union[TemplateDataFile, Dict[str, Any]]): The data configuration (file schema or raw dictionary).
            template_data_dir (Optional[str], optional): Base directory for file handlers. Overrides the instance default if provided.
        """
        assert hasattr(self,"renderer") and self.renderer is not None
        handler = TemplateDataHandlerFactory.getHandler(type(data),template_data_dir)
        template_data = handler.extractData(data,self.partials,self.extra_renderers)
        for prefix,renderer in self.extra_renderers.items():
            if hasattr(renderer, "exposed"):
                self.template_data.update(renderer.exposed)
        self.template_data.update(template_data)
        self.processPlugins()

    def copyPartials( self, base_dir:str, pages_dir:str ) -> None:
        """
        Copies all assets (partials) referenced in `self.partials` to the local output structure.
        It updates the template data to hold the relative paths of the copied assets, making them accessible from the rendered document.

        Args:
            base_dir (str): The base directory for asset deployment.
            pages_dir (str): The directory where the rendered pages are saved. Used to calculate relative paths.
        """
        for prefix, path in self.partials.items():
            local_partial_path = os.path.join(base_dir,prefix)
            shutil.copytree(path, local_partial_path)
            self.updateTemplateData({prefix:os.path.relpath(local_partial_path,pages_dir)})

    def renderExtra( self, base_dir:str ) -> None:
        """
        Renders all extra renderers associated with this view.
        Each extra renderer is expected to have its own rendering logic and output path.

        Args:
            output_dirpath (str): The base directory where extra rendered outputs should be saved.
        """
        extra_renders = []
        for prefix,renderer in self.extra_renderers.items():
            output_filepath = renderer.render( base_dir )
            self.updateTemplateData({prefix:os.path.relpath(output_filepath,base_dir)})
            extra_renders.append(os.path.relpath(output_filepath,base_dir))
        self.updateTemplateData({"extra_renders":extra_renders})

    def render( self, output_dirpath:str, filename:Optional[str] = None ) -> None:
        """ Executes the final rendering step, writing the output to a file.

        Args:
            output_dirpath (str): The directory where the rendered file should be saved.
            filename (Optional[str], optional): The specific filename for the output. If None, `self.out_filename` is used. Defaults to None.
        Raises:
            ValueError: If the filename is not set on the instance or provided as an argument.
            FileNotFoundError: If the output directory cannot be created.
        """
        filename = filename or self.out_filename
        if not filename:
            raise ValueError(f"Filename must be set")
        if not os.path.isdir(output_dirpath):
            os.mkdir(output_dirpath)

        self.renderer.render(os.path.join(output_dirpath,filename),self.template_data)

    def processPlugins( self ) -> None:
        """
        Runs all registered plugins against the current template data.
        Each plugin processes the data and its result is merged back into `self.template_data`.
        """
        for plugin in self.plugins:
            self.template_data.update(plugin.process(self.template_data))

class ViewFactory:
    """ Factory class for creating initialized `View` instances based on a component type. """
    @staticmethod
    def create(
        component_type:str,
        template_info:TemplateInfo,
        template_data_dir:Optional[str] = None,
        component_id:Optional[str] = None
    ) -> View:
        """
        Creates a new `View` instance, pre-configured with default settings based on the component type.

        Args:
            component_type (str): The type of component to create a view for ("home", "node", or "leaf").
            template_info (TemplateInfo): Schema object with template configuration and data sources.
            template_data_dir (Optional[str], optional): Base directory for resolving data file paths. Defaults to None.
            component_id (Optional[str], optional): The unique identifier for the component (used for titles/paths). Defaults to None.
        Returns:
            View: A fully configured View instance ready for rendering.
        Raises:
            NotImplementedError: If the provided `component_type` is not supported.
        """
        template_type_map = dict(
            home = dict(
                base_template_data = dict(
                    title = "My Dashboard",
                    datetime = datetime.strftime(datetime.now(),format="%Y-%m-%d:%H:%M:%S")
                ),
                filename = "index.adoc",
            ),
            node = dict(
                base_template_data = dict(
                    title = "Default Repository",
                    description = "Default Description",
                    self_id_path = component_id or "default_repository",
                    parent_ids = "dashboard_index",
                    card_image = f"ROOT:{component_id}.jpg" if component_id else "ROOT:default-image.jpg",
                ),
                filename = "index.adoc"
            ),
            leaf = dict(
                base_template_data = dict(
                    title = component_id or "Default Leaf",
                    self_id_path = "default_leaf",
                    parent_ids = "dashboard_index",
                    description = "Default Leaf Description",
                    card_image = "ROOT:default-image.jpg"
                ),
                filename = "leaf.adoc",
            )
        )
        if component_type not in template_type_map:
            raise NotImplementedError(f"Component type {component_type} not implemented")

        return View(
            component_type,
            template_info,
            template_data_dir,
            template_type_map[component_type]["base_template_data"],
            template_type_map[component_type]["filename"]
        )


class PreRenderPlugin:
    """
    Interface (abstract base class) for a plugin that processes and modifies template data.
    Plugins are executed before the final rendering to enrich or transform the data context.
    """
    def process(self, template_data: Dict[str,Any]) -> Dict[str,Any]:
        """
        Processes the template data and returns a dictionary of new or modified data to be merged back.

        Args:
            template_data (Dict[str, Any]): The current template data dictionary.
        Returns:
            Dict[str, Any]: A dictionary containing data updates.
        Raises:
            NotImplementedError: If the method is not implemented in a derived class.
        """
        raise NotImplementedError