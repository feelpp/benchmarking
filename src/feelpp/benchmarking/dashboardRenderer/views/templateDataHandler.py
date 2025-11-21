
from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import TemplateInfo,TemplateDataFile
from feelpp.benchmarking.json_report.renderer import JsonReportController
import json, os, warnings
from typing import Union, Dict,Any

class DataHandler:
    """
    Abstract base class defining the interface for data extraction.

    Concrete subclasses must implement the `extractData` method to define how
    template data is sourced and prepared, based on the data's type.
    """
    def extractData( self, data: Union[TemplateDataFile, Dict[str,Any]], partials:Dict[str,Any] = {}, extra_renderers = {}) -> Dict[str,Any]:
        """
        Extracts and prepares data for use in a template renderer.
        Args:
            data (Union[TemplateDataFile, Dict[str, Any]]): The input data specification, which can be a file configuration (`TemplateDataFile`) or a dictionary of data.
            partials (Dict[str, Any], optional): A dictionary used to store references to files that need to be copied later (e.g., assets). Defaults to {}.
        Returns:
            Dict[str, Any]: A dictionary containing the extracted data to be passed to the template context.
        Raises:
            NotImplementedError: If the method is not implemented in a derived class.
        """
        raise NotImplementedError("Pure virtual method")

class TemplateDataFileHandler(DataHandler):
    """
    Concrete handler for extracting data specified by a `TemplateDataFile` schema object.
    This handler manages reading data from local files (e.g., JSON) or marking files for later copying (e.g., assets).
    """
    def __init__( self, template_data_dir:str = None ):
        """
        Args:
            template_data_dir (Optional[str], optional): The base directory where template data files are located. This is used to resolve relative paths. Defaults to None.
        """
        self.template_data_dir = template_data_dir

    def extractData( self, data: TemplateDataFile, partials:Dict[str,Any] = {}, extra_renderers = {} ) -> Dict[str,Any]:
        """
        Extracts data from a file or marks a file for copying based on the `TemplateDataFile` action.

        Args:
            data (TemplateDataFile): The configuration object specifying the file path, format, action ("input" or "copy"), and optional prefix.
            partials (Dict[str, Any], optional): The dictionary to store file paths marked for copying when the action is "copy". Defaults to {}.
        Returns:
            Dict[str, Any]: The extracted data dictionary for template context (only non-empty if action is "input").
        Raises:
            UserWarning: If a file specified by `filepath` does not exist and the action is "input".
            JSONDecodeError: If the file content is not valid JSON.
        """
        filepath = os.path.join( self.template_data_dir, data.filepath ) if self.template_data_dir else data.filepath
        if data.action == "input":
            if not os.path.exists( filepath ):
                warnings.warn(f"{filepath} does not exist. Skipping")
                return {}
            with open( filepath, "r" ) as f:
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

        elif data.action == "json2adoc":
            controller = JsonReportController(filepath, output_format="adoc")
            extra_renderers[data.prefix] = controller
            return {}


class DictDataHandler(DataHandler):
    """
    Concrete handler for data already provided as a raw Python dictionary.

    This handler performs no external file operations, simply returning the input dictionary.
    """
    def extractData(self, data: dict, partials:dict = {}, extra_renderers = {}) -> dict:
        """ Extracts data by returning the input dictionary directly.
        Args:
            data (Dict[str, Any]): The input dictionary data.
            partials (Dict[str, Any], optional): Not used by this handler. Defaults to {}.
        Returns:
            Dict[str, Any]: The input dictionary data.
        """
        return data

class TemplateDataHandlerFactory:
    """
    Factory class for creating the appropriate DataHandler based on the type of the data configuration object.
    """
    @staticmethod
    def getHandler( data_type: type, template_data_dir:str = None ) -> DataHandler:
        """
        Returns a concrete DataHandler instance based on the input data type.

        Args:
            data_type (Type): The Python type of the data configuration object (e.g., `TemplateDataFile` or `dict`).
            template_data_dir (Optional[str], optional): Base directory for file handlers. Defaults to None.
        Returns:
            DataHandler: An instance of `TemplateDataFileHandler` or `DictDataHandler`.
        Raises:
            NotImplementedError: If the provided `data_type` is not supported.
        """
        if data_type is TemplateDataFile:
            return TemplateDataFileHandler(template_data_dir)
        elif data_type is dict:
            return DictDataHandler()
        else:
            raise NotImplementedError(f"Unsupported data type for template data : {data_type}")
