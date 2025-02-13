from jinja2 import Environment, FileSystemLoader
import os
from pathlib import Path

class TemplateRenderer:
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
        self.env.filters["inttouniquestr"] = self.intToUniqueStr

    @staticmethod
    def stripQuotes(value):
        if isinstance(value,str):
            return value.strip('"')
        return value

    @staticmethod
    def intToUniqueStr(n):
        s = []
        while n:
            n, r = divmod(n - 1, 26)
            s.append(chr(65 + r))
        return "".join(reversed(s))

class TemplateRendererFactory:
    TEMPLATES = {
        "home": "home.adoc.j2",
        "index": "index.adoc.j2"
    }

    @classmethod
    def create(cls, renderer_type: str) -> TemplateRenderer:
        if renderer_type not in cls.TEMPLATES:
            raise ValueError(
                f"Renderer type '{renderer_type}' not recognized. Valid options are: {', '.join(cls.TEMPLATES.keys())}."
            )
        template_dir = str(Path(__file__).resolve().parent)
        return TemplateRenderer(template_dir, cls.TEMPLATES[renderer_type])