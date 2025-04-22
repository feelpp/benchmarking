
from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import TemplateInfo,TemplateDataFile
import json, os
from typing import Union

class DataHandler:
    def extractData(self, data: Union[TemplateDataFile, dict], partials:dict = {}) -> dict:
        raise NotImplementedError("Pure virtual method")

class TemplateDataFileHandler(DataHandler):
    def __init__(self,template_data_dir:str = None):
        self.template_data_dir = template_data_dir

    def extractData(self, data: TemplateDataFile, partials:dict = {}) -> dict:
        filepath = os.path.join(self.template_data_dir,data.filepath) if self.template_data_dir else data.filepath
        if data.action == "input":
            with open(filepath,"r") as f:
                if data.format == "json":
                    template_data = json.load(f)
            if data.prefix:
                return {data.prefix: template_data}
            return template_data
        elif data.action == "copy":
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"{filepath} does not exist")
            partials[data.prefix] = filepath
            return {}


class DictDataHandler(DataHandler):
    def extractData(self, data: dict, partials:dict = {}) -> dict:
        return data

class TemplateDataHandlerFactory:
    @staticmethod
    def getHandler(data_type: type, template_data_dir:str = None) -> DataHandler:
        if data_type is TemplateDataFile:
            return TemplateDataFileHandler(template_data_dir)
        elif data_type is dict:
            return DictDataHandler()
        else:
            raise NotImplementedError("Unsupported data type for template data.")
