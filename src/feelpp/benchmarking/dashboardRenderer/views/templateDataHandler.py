
from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import TemplateInfo,TemplateDataFile
import json, os, warnings
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
            if not os.path.exists(filepath):
                warnings.warn(f"{filepath} does not exist. Skipping")
                return {}
            with open(filepath,"r") as f:
                content = f.read()
                if data.format == "json":
                    if not content:
                        content = "{}"
                    template_data = json.loads(content)
            if data.prefix:
                return {data.prefix: template_data}
            return template_data
        elif data.action == "copy":
            if os.path.exists(filepath):
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
            raise NotImplementedError(f"Unsupported data type for template data : {data_type}")
