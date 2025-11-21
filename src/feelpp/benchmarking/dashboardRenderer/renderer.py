from jinja2 import Environment, FileSystemLoader
import os
from pathlib import Path
from feelpp.benchmarking.dashboardRenderer.plugins.figures.controller import Controller as FiguresController
from typing import List,Union,Dict,Any

class TemplateRenderer:
    """
    Base Class to render structured data (like JSON) to text files (e.g., AsciiDoc)
    using Jinja2 templates.

    This class sets up the Jinja2 environment, loads a specific template, and
    configures custom globals and filters for use within the templates.
    """

    def __init__( self, template_paths: Union[List[str],str], template_filename:str ):
        """ Initialize the template for the renderer by configuring the Jinja2 environment.
        Args:
            template_paths (List[str]): A list of local directory paths where Jinja2 templates (`.j2` files) are located.
            template_filename (str): The name of the specific template file to load and use for the primary rendering (e.g., "home.adoc.j2").
        """
        self.env = Environment( loader=FileSystemLoader( template_paths ), trim_blocks=True, lstrip_blocks=True )
        self.setGlobals()
        self.setFilters()
        self.template = self.env.get_template( template_filename )


    def render( self, output_filepath:str, data:Dict[str,Any]={} ) -> None:
        """
        Render the provided data into the primary template and write the output to the specified file path.

        A special variable, 'self_dirpath', is added to the data, which contains the directory of the output file for relative path calculations in the template.

        Args:
            output_filepath (str): The full path to the output file (e.g., `report.adoc`).
            data (Dict[str, Any], optional): The context data dictionary passed to the template. Defaults to an empty dictionary.
        """

        data.update({"self_dirpath":os.path.dirname(output_filepath)})
        with open( output_filepath, 'w' ) as f:
            f.write( self.template.render(data) )

    def setGlobals( self ) -> None:
        """Configures global variables available to all templates loaded by this environment."""
        self.env.globals.update( { "FiguresController":FiguresController } )
        self.env.globals["renderTemplate"] = self.renderTemplate

    def setFilters( self ) -> None:
        """ Configures custom filters available for use within all templates. """
        self.env.filters["stripquotes"] = self.stripQuotes

    @staticmethod
    def stripQuotes( value:Any ) -> Any:
        """ Jinja2 filter to remove double quotes from the start and end of a string.
        If the value is not a string, it is returned unchanged.

        Args:
            value (Any): The input value, potentially a string with surrounding quotes.
        Returns:
            Any: The string with quotes stripped, or the original value if not a string.
        """
        if isinstance( value, str ):
            return value.strip('"')
        return value

    def renderTemplate( self, template_path:str, data:Dict[str,Any], destination:str ) -> None:
        """
        Renders an arbitrary, secondary template file within the environment to a specific destination.

        This method is registered as a global function within the Jinja2 environment, allowing templates to dynamically render other templates into the output.

        Args:
            template_path (str): The name of the template file to render (e.g., 'sub_page.j2').
            data (Dict[str, Any]): The context data for the template.
            destination (str): The full path to the file where the rendered output will be written.
        """
        template = self.env.get_template( template_path )
        dest_dir = os.path.dirname( destination )
        if not os.path.isdir( dest_dir ):
            os.makedirs( dest_dir )
        with open( destination, 'w' ) as f:
            f.write( template.render( data ) )

class BaseRendererFactory:
    """
    Factory class responsible for creating and configuring specific TemplateRenderer instances.
    It determines the correct template filename based on the requested renderer type and configures the template lookup paths.
    """
    DEFAULT_MV = {
        "home": { "template":"home.adoc.j2" },
        "node":{ "template": "node.adoc.j2" },
        "leaf":{ "template":"leaf.adoc.j2" }
    }

    @classmethod
    def create( cls, renderer_type: str, extra_templated_dir:str = None ) -> TemplateRenderer:
        """
        Creates a configured TemplateRenderer instance for a specific renderer type.
        Args:
            renderer_type (str): The type of renderer requested ("home", "node", or "leaf").
            extra_templated_dir (Optional[str]): An optional path to an additional directory to search for templates (e.g., for custom templates).
        Returns:
            TemplateRenderer: An initialized instance of TemplateRenderer.
        Raises:
            ValueError: If the `renderer_type` is not one of the recognized default types.
        """
        if renderer_type not in cls.DEFAULT_MV:
            raise ValueError(
                f"Renderer type '{renderer_type}' not recognized. Valid options are: {', '.join(cls.DEFAULT_MV.keys())}."
            )
        template_dirs = [os.path.join(Path(__file__).resolve().parent,"templates")]
        if extra_templated_dir:
            template_dirs += [extra_templated_dir]
        return TemplateRenderer(
            template_dirs,
            cls.DEFAULT_MV[renderer_type]["template"]
        )