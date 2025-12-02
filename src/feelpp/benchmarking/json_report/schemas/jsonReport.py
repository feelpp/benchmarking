from typing import Literal, Union, Optional, List, Dict, Annotated, Callable, Any
from pydantic import ValidationError, BaseModel, field_validator, model_validator, Field, ConfigDict
from datetime import datetime
from feelpp.benchmarking.json_report.figures.schemas.plot import Plot
from feelpp.benchmarking.json_report.tables.schemas.tableSchema import Table
from feelpp.benchmarking.json_report.text.schemas.textSchema import Text
from feelpp.benchmarking.json_report.schemas.dataRefs import DataFile

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
    table: Optional[Table] = Table()
    filter: Optional[FilterInput] = None

class ListNode(ReportNode):
    type:Literal["itemize"]
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
    contents: List[Node]



class JsonReportSchema(BaseModel):
    title: Optional[str] = None
    datetime: Optional[str] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data: Optional[List[Union[DataFile]]] = []
    model_config = ConfigDict( extra='allow' )

    contents: Optional[List[Annotated[Node, Field(discriminator="type")]]] = []

    @model_validator(mode="before")
    @classmethod
    def coerceListInput( cls, values ):
        if not values:
            return values

        if isinstance(values, list):
            contents = []
            for item in values:
                try:
                    node = PlotNode.model_validate({"type":"plot", "plot":item})
                except ValidationError:
                    node = item
                contents.append(node)
            return {"contents": contents}
        elif isinstance(values, dict):
            return values
        else:
            raise TypeError(f"Expected dict or list at root, got {type(values)}")

    def flattenContent(self, contents = None) -> list[Node]:
        flattened = []
        if contents is None:
            contents = self.contents
        for node in contents:
            if node.type == "section":
                flattened += self.flattenContent(node.contents)
            else:
                flattened.append(node)
        return flattened