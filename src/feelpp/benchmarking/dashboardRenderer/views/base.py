from typing import Union
import os, json
from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import TemplateInfo,TemplateDataFile
from feelpp.benchmarking.dashboardRenderer.renderer import BaseRendererFactory, TemplateRenderer


class DataHandler:
    def extractData(self, data: Union[TemplateDataFile, dict]) -> dict:
        raise NotImplementedError("Pure virtual method")

class TemplateDataFileHandler(DataHandler):
    def __init__(self,template_data_dir:str = None):
        self.template_data_dir = template_data_dir

    def extractData(self, data: TemplateDataFile) -> dict:
        filepath = os.path.join(self.template_data_dir,data.filepath) if self.template_data_dir else data.filepath
        with open(filepath,"r") as f:
            if data.format == "json":
                template_data = json.load(f)
        if data.prefix:
            return {data.prefix: template_data}
        return template_data

class DictDataHandler(DataHandler):
    def extractData(self, data: dict) -> dict:
        return data

class TemplateDataHandlerFactory:
    @staticmethod
    def getHandler(data: Union[TemplateDataFile, dict],template_data_dir:str = None) -> DataHandler:
        if isinstance(data, TemplateDataFile):
            return TemplateDataFileHandler(template_data_dir)
        elif isinstance(data, dict):
            return DictDataHandler()
        else:
            raise NotImplementedError("Unsupported data type for template data.")

class View:
    def __init__(self,template_info:TemplateInfo, template_data_dir:str = None) -> None:
        self.renderer = self.initRenderer(template_info.template)
        if template_info.template:
            self.addExtraTemplate(template_info.template)
        for data in template_info.data:
            self.updateTemplateData(data,template_data_dir)

    def initRenderer(self,template = None, base_type=None):
        renderer = BaseRendererFactory.create(
            base_type,
            os.path.dirname(template) if template else None
        )
        renderer = self.initBaseTemplateData(renderer)
        return renderer

    def initBaseTemplateData(self,renderer:TemplateRenderer) -> TemplateRenderer:
        raise NotImplementedError("Pure virtual method. Do not call...")

    def addExtraTemplate(self,template):
        if "extra_templates" not in self.renderer.template_data:
            self.renderer.template_data["extra_templates"] = []
        self.renderer.template_data["extra_templates"].append(os.path.basename(template))

    def updateTemplateData(self,data:Union[TemplateDataFile,dict],template_data_dir:str = None):
        assert hasattr(self,"renderer") and self.renderer is not None
        handler = TemplateDataHandlerFactory.getHandler(data,template_data_dir)
        template_data = handler.extractData(data)
        self.renderer.template_data.update(template_data)

    def render(self,output_dirpath,filename):

        if not os.path.isdir(output_dirpath):
            os.mkdir(output_dirpath)

        self.renderer.render(os.path.join(output_dirpath,filename))

