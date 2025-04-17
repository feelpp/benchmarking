from jinja2 import Environment, FileSystemLoader
import os
from pathlib import Path
from datetime import datetime

class TemplateRenderer:
    """ Base Class to render the JSON files to AsciiDoc files using Jinja2 templates"""
    plugins = {}

    def __init__(self, template_paths, template_filename, template_data:dict={}):
        """ Initialize the template for the renderer
        Args:
            template_path (list[str]): The paths to the Jinja2 template folders
            template_filename (str): The template filename
        """
        self.env = Environment(loader=FileSystemLoader(template_paths), trim_blocks=True, lstrip_blocks=True)
        self.setGlobals()
        self.setFilters()
        self.template = self.env.get_template(template_filename)
        self.template_data = template_data


    def render(self, output_filepath, data={}):
        """ Render the JSON file to an AsciiDoc file using a Jinja2 template and the given data"""

        new_data = self.template_data.copy()
        new_data.update(data)
        with open(output_filepath, 'w') as f:
            f.write(self.template.render(new_data))

    def setGlobals(self):
        """ Set environment globals """
        self.env.globals.update(zip=zip)
        self.env.globals.update(self.plugins)

    def setFilters(self):
        """ Set environment filters """
        self.env.filters["stripquotes"] = self.stripQuotes
        self.env.filters["inttouniquestr"] = self.intToUniqueStr

    @classmethod
    def addPlugin(cls,plugin_name,plugin):
        cls.plugins[plugin_name] = plugin

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



class BaseRendererFactory:
    DEFAULT_MV = {
        "home": {
            "template":"home.adoc.j2",
            "data":dict(
                title = "My Dashboard",
                datetime = datetime.strftime(datetime.now(),format="%Y-%m-%d:%H:%M:%S")
            ),
        },
        "node":{
            "template": "node.adoc.j2",
            "data":dict(
                title = "Default Repository",
                self_id = "default_repository",
                parent_ids = "dashboard_index",
                description = "Default Description",
                card_image = "ROOT:default-image.jpg"
            ),
        },
        "leaf":{
            "template":"leaf.adoc.j2",
            "data":dict(
                title = "Default Leaf",
                self_id = "default_leaf",
                parent_ids = "dashboard_index",
                description = "Default Leaf Description",
                card_image = "ROOT:default-image.jpg"
            )
        }
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
            cls.DEFAULT_MV[renderer_type]["template"],
            cls.DEFAULT_MV[renderer_type]["data"].copy()
        )