
from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import TemplateInfo,TemplateDataFile
import json, os
from typing import Union

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
