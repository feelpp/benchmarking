from jinja2 import Environment, FileSystemLoader
import os

class Renderer:
    """ Base Class to render the JSON files to AsciiDoc files using Jinja2 templates"""

    def __init__(self, template_path, template_filename):
        """ Initialize the template for the renderer
        Args:
            template_path (str): The path to the Jinja2 template folder
            template_filename (str): The template filename
        """
        self.env = Environment(loader=FileSystemLoader(template_path), trim_blocks=True, lstrip_blocks=True)
        self.setGlobals()
        self.setFilters()
        self.template = self.env.get_template(template_filename)

    def render(self, output_filepath, data):
        """ Render the JSON file to an AsciiDoc file using a Jinja2 template and the given data"""
        with open(output_filepath, 'w') as f:
            f.write(self.template.render(data))

    def setGlobals(self):
        """ Set environment globals """
        self.env.globals.update(zip=zip)

    def setFilters(self):
        """ Set environment filters """
        self.env.filters["stripquotes"] = self.stripQuotes

    @staticmethod
    def stripQuotes(value):
        if isinstance(value,str):
            return value.strip('"')
        return value

class RendererFactory:
    @staticmethod
    def create(renderer_type):
        base = "./src/feelpp/benchmarking/report/templates/"
        templates = {
            "index" : "index.adoc.j2",
            "benchmark" : "benchmark.adoc.j2",
            "atomic_overview" : "atomicOverview.adoc.j2"
        }
        try:
            return Renderer(base, templates[renderer_type])
        except KeyError:
            raise NotImplementedError(
                f"'{renderer_type}' not recognized. Valid options are: {', '.join(templates.keys())}."
            )