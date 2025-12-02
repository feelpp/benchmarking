from typing import Literal, Union, Optional, List, Dict, Annotated, Callable, Any
from pydantic import ValidationError, BaseModel, field_validator, model_validator, Field, ConfigDict
from datetime import datetime
import os, warnings
import importlib.util

from feelpp.benchmarking.json_report.figures.schemas.plot import Plot
from feelpp.benchmarking.json_report.tables.schemas.tableSchema import Table
from feelpp.benchmarking.json_report.text.schemas.textSchema import Text

class ReportNode(BaseModel):
    type:str
    ref: Optional[str] = None


class TextNode(ReportNode):
    type:Literal["text"]
    text: Text

class LatexNode(ReportNode):
    type:Literal["latex"]
    latex: str

class ImageNode(ReportNode):
    type:Literal["image"]
    src: str
    caption: Optional[str] = None
    alt: Optional[str] = None


class FilterInput(BaseModel):
    placeholder: Optional[str] = "Filter..."
    style:Optional[str] = "margin-bottom:0.5em;padding:0.3em;width:50%;"

class PlotNode(ReportNode):
    type: Literal["plot"]
    plot: Plot

class TableNode(ReportNode):
    type: Literal["table"]
    title: Optional[str] = None
    table: Table
    filter: Optional[FilterInput] = None

class ListNode(ReportNode):
    type:Literal["list"]
    items:List[Union[TextNode,Text,str]]

    @model_validator(mode="after")
    def coerceItemsText(self):
        parsedItems = []
        for item in self.items:
            if isinstance(item,str) or isinstance(item, Text):
                parsedItems.append(TextNode.model_validate({"type":"text","text":Text.model_validate(item),"ref":self.ref}))
            elif isinstance(item,TextNode):
                if not item.ref:
                    item.ref = self.ref
                parsedItems.append(item)
        self.items = parsedItems
        return self

Node = Union[TextNode, "SectionNode", PlotNode, LatexNode, ImageNode, TableNode, ListNode]

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

    @field_validator("module",mode="after")
    @classmethod
    def setPreprocessorModule( cls, module, info ):
        if isinstance(module,str):
            try:
                module = __import__( module, fromlist=[info.data.get("function")] )
            except ImportError as e:
                if not os.path.isabs(module):
                    report_filepath = info.context.get("report_filepath", None)
                    if not report_filepath:
                        raise FileNotFoundError(f"Cannot resolve the report file path {report_filepath}")
                    report_filepath = os.path.abspath(report_filepath)

                    module = os.path.abspath( os.path.join( os.path.dirname(report_filepath), module ) )

                spec = importlib.util.spec_from_file_location(module,module)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                module = mod

        return module

    @field_validator("function",mode="after")
    def setPreprocessorFunction( cls, function, info ):
        if isinstance(function,str):
            try:
                if not hasattr( info.data["module"], function ):
                    raise AttributeError(f"Preprocessor function {function} not found in module {info.data.get('module')}.")
                function = getattr( info.data["module"], function )
            except AttributeError as e:
                raise AttributeError(f"Preprocessor function '{function}' could not be set: {e}")

        return function

    def apply(self, filedata: Any) -> Any:
        return self.function(filedata)


class DataFile(BaseModel):
    name: str
    filepath: str
    format: Optional[Literal["json","csv","raw"]] = None
    preprocessor: Optional[Preprocessor] = None
    expose:Optional[Union[str,bool]] = True

    @model_validator(mode="after")
    def coerceExpose(self):
        if self.expose and isinstance(self.expose,bool):
            self.expose = self.name
        return self


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

    @field_validator("preprocessor",mode="before")
    @classmethod
    def passContext(cls, v:Preprocessor, info):
        if v:
            return Preprocessor.model_validate(v,context=info.context)
        return v


class JsonReportSchema(BaseModel):
    title: Optional[str] = None
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