from jinja2 import Environment, FileSystemLoader
import os
from pathlib import Path
from feelpp.benchmarking.dashboardRenderer.plugins.figures.controller import Controller

class TemplateRenderer:
    """ Base Class to render the JSON files to AsciiDoc files using Jinja2 templates"""

    def __init__(self, template_paths, template_filename):
        """ Initialize the template for the renderer
        Args:
            template_path (list[str]): The paths to the Jinja2 template folders
            template_filename (str): The template filename
        """
        self.env = Environment(loader=FileSystemLoader(template_paths), trim_blocks=True, lstrip_blocks=True)
        self.setGlobals()
        self.setFilters()
        self.template = self.env.get_template(template_filename)


    def render(self, output_filepath, data={}):
        """ Render the JSON file to an AsciiDoc file using a Jinja2 template and the given data"""

        data.update({"self_dirpath":os.path.dirname(output_filepath)})
        with open(output_filepath, 'w') as f:
            f.write(self.template.render(data))

    def setGlobals(self):
        """ Set environment globals """
        self.env.globals.update({
            "FiguresController":Controller
        })
        self.env.globals["renderTemplate"] = self.renderTemplate

    def setFilters(self):
        """ Set environment filters """
        self.env.filters["stripquotes"] = self.stripQuotes

    @staticmethod
    def stripQuotes(value):
        if isinstance(value,str):
            return value.strip('"')
        return value

    def renderTemplate(self,template_path, data, destination):
        template = self.env.get_template(template_path)
        dest_dir = os.path.dirname(destination)
        if not os.path.isdir(dest_dir):
            os.makedirs(dest_dir)
        with open(destination, 'w') as f:
            f.write(template.render(data))

class BaseRendererFactory:
    DEFAULT_MV = {
        "home": { "template":"home.adoc.j2" },
        "node":{ "template": "node.adoc.j2" },
        "leaf":{ "template":"leaf.adoc.j2" }
    }

    @classmethod
    def create(cls, renderer_type: str, extra_templated_dir:str = None) -> TemplateRenderer:
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