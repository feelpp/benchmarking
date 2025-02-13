from feelpp.benchmarking.dashboardRenderer.renderer import TemplateRenderer
from pathlib import Path
from datetime import datetime
import os

class Controller:
    def __init__(self, renderer:TemplateRenderer, template_data:dict, output_filename:str):
        self.renderer = renderer
        self.template_data = template_data

        self.output_filename = output_filename

    def render(self,output_dirpath):
        self.renderer.render(os.path.join(output_dirpath,self.output_filename),self.template_data)

    def updateData(self,new_data):
        self.template_data.update(new_data)



class DefaultControllerFactory:
    DEFAULT_MV = {
        "home": {
            "template":"home.adoc.j2",
            "filename":"index.adoc",
            "data":dict(
                title = "My Dashboard",
                datetime = datetime.strftime(datetime.now(),format="%Y-%m-%d:%H:%M:%S")
            ),
        },
        "index":{
            "template": "index.adoc.j2",
            "filename":"index.adoc",
            "data":"",
        }
    }

    @classmethod
    def create(cls, renderer_type: str) -> TemplateRenderer:
        if renderer_type not in cls.DEFAULT_MV:
            raise ValueError(
                f"Renderer type '{renderer_type}' not recognized. Valid options are: {', '.join(cls.DEFAULT_MV.keys())}."
            )
        template_dir = os.path.join(Path(__file__).resolve().parent,"templates")
        renderer = TemplateRenderer(template_dir, cls.DEFAULT_MV[renderer_type]["template"])

        return Controller(renderer,cls.DEFAULT_MV[renderer_type]["data"],cls.DEFAULT_MV[renderer_type]["filename"])