from typing import Literal, Union, Optional, List, Dict, Annotated, Callable, Any
from pydantic import ValidationError, BaseModel, field_validator, model_validator, Field, ConfigDict
from datetime import datetime
import os, warnings
import importlib.util
from feelpp.benchmarking.json_report.figures.schemas.plot import Plot

class ReportNode(BaseModel):
    type:str
    data: Optional[str] = None


class TextNode(ReportNode):
    type:Literal["text"]
    text: str

class LatexNode(ReportNode):
    type:Literal["latex"]
    latex: str

class ImageNode(ReportNode):
    type:Literal["image"]
    src: str
    caption: Optional[str] = None
    alt: Optional[str] = None

class PlotNode(ReportNode):
    type: Literal["plot"]
    plot: Plot

Node = Union[TextNode, "SectionNode", PlotNode, LatexNode, ImageNode]

class SectionNode(ReportNode):
    type:Literal["section"]
    title:str
    content: List[Node]


class Preprocessor(BaseModel):
    #TODO: IMPORTANT: VERIFY SECURITY IMPLICATIONS OF DYNAMIC IMPORTS
    # Maybe support class later and/or static methods
    module:str
    function:str

    @model_validator(mode="before")
    @classmethod
    def parsePreprocessorString( cls, values ):
        if isinstance(values, str):
            if ":" not in values:
                raise ValueError(f"Preprocessor string '{values}' must be of the form 'module:function'")
            module, function = values.split(":",1)
            return {"module":module, "function":function}
        elif isinstance(values, dict):
            return values
        else:
            raise TypeError(f"Expected str or dict for Preprocessor, got {type(values)}")

    @model_validator(mode="after")
    def setPreprocessor( self ):
        try:
            self.module = __import__( self.module, fromlist=[self.function] )
        except ImportError as e:
            try:
                spec = importlib.util.spec_from_file_location(self.module,self.module)
                self.module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(self.module)
            except Exception as e:
                raise ImportError(f"Preprocessor module '{self.module}' could not be imported: {e}")


        try:
            if not hasattr( self.module, self.function ):
                raise AttributeError(f"Preprocessor function '{self.function}' not found in module '{self.module}'.")
            self.function = getattr( self.module, self.function )
        except AttributeError as e:
            raise AttributeError(f"Preprocessor function '{self.function}' could not be set: {e}")
        return self

    def apply(self, filedata: Any) -> Any:
        return self.function(filedata)


class DataFile(BaseModel):
    name: str
    filepath: str
    format: Optional[Literal["json","csv","raw"]] = None
    preprocessor: Optional[Preprocessor] = None

    @field_validator("filepath", mode="after")
    @classmethod
    def validateAndResolveFilepath(cls, filepath, info):
        if os.path.isabs(filepath):
            if not os.path.exists(filepath):
                warnings.warn(f"DataFile filepath '{filepath}' does not exist.")
                filepath = None
        else:
            report_filepath = info.context.get("report_filepath", None)
            if not report_filepath:
                raise FileNotFoundError("Cannot resolve the report file path ")
            report_filepath = os.path.abspath(report_filepath)
            filepath = os.path.abspath( os.path.join( os.path.dirname(report_filepath), filepath ) )
            if not os.path.exists(filepath):
                warnings.warn(f"DataFile filepath '{filepath}' does not exist relative to report file '{report_filepath}'.")
                filepath = None

        return filepath

    @model_validator(mode="before")
    @classmethod
    def inferFormat( cls, values ):
        if "filepath" in values and "format" not in values:
            _, ext = os.path.splitext( values["filepath"] )
            ext = ext.lower()
            ext = ext.lstrip(".").lower()
            values["format"] = ext
        return values


class JsonReportSchema(BaseModel):
    title: Optional[str] = "Report"
    datetime: Optional[str] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data: Optional[List[Union[DataFile]]] = []
    model_config = ConfigDict( extra='allow' )

    content: Optional[List[Annotated[Node, Field(discriminator="type")]]] = []

    @model_validator(mode="before")
    @classmethod
    def coerceListInput( cls, values ):
        if not values:
            return values

        if isinstance(values, list):
            content = []
            for item in values:
                try:
                    node = PlotNode.model_validate({"type":"plot", "plot":item})
                except ValidationError:
                    node = item
                content.append(node)
            return {"content": content}
        elif isinstance(values, dict):
            return values
        else:
            raise TypeError(f"Expected dict or list at root, got {type(values)}")

    def flattenContent(self, content = None) -> list[Node]:
        flattened = []
        if content is None:
            content = self.content
        for node in content:
            if node.type == "section":
                flattened += self.flattenContent(node.content)
            else:
                flattened.append(node)
        return flattened