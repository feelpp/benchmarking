from typing import Literal, Union, Optional, List, Dict, Annotated, Callable, Any
from pydantic import ValidationError, BaseModel, field_validator, model_validator, Field, ConfigDict
from datetime import datetime
from feelpp.benchmarking.json_report.figures.schemas.plot import Plot
from feelpp.benchmarking.json_report.tables.schemas.tableSchema import TableLayout, TableStyle, FilterInput
from feelpp.benchmarking.json_report.text.schemas.textSchema import Text
from feelpp.benchmarking.json_report.schemas.dataRefs import DataTable, DataObject, DataRaw, DataField, DataRef

class ReportNode(BaseModel):
    type:str
    ref: Optional[str] = None

    model_config = ConfigDict( extra="forbid" )


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
    style: Optional[List[str]] = ["img-fluid"]

class PlotNode(ReportNode):
    type: Literal["plot"]
    plot: Plot



class TableNode(ReportNode):
    type: Literal["table"]
    layout: Optional[TableLayout] = TableLayout()
    filter: Optional[FilterInput] = None
    style: Optional[TableStyle] = TableStyle()

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

Node = Union[TextNode, "SectionNode", PlotNode, LatexNode, ImageNode, TableNode, ListNode, "GridNode"]

class SectionNode(ReportNode):
    type:Literal["section"]
    title:str
    contents: Optional[List[Node]] = []

class GridNode(ReportNode):
    type: Literal["grid"]
    contents: Optional[List[Node]] = []
    columns: Optional[int] = 1
    justify: Optional[Literal["start","center","end"]] = "start"
    align: Optional[Literal["start","center","end"]] = "start"
    gap: Optional[int] = 2

    @field_validator("columns",mode="after")
    @classmethod
    def validateColumns(cls,v):
        if v < 1 or v > 4:
            raise ValueError(f"Number of columns must be between 1 and 4. Got : {v}")
        return v

    @field_validator("gap",mode="after")
    @classmethod
    def validateGap(cls,v):
        if v < 1 or v > 3:
            raise ValueError(f"Gap must be between 1 and 3. Got : {v}")
        return v

DataTypes = Union[DataTable, DataObject, DataRaw, DataRef]

class JsonReportSchema(BaseModel):
    title: Optional[str] = None
    datetime: Optional[str] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data: Optional[List[DataTypes]] = []
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