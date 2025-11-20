from typing import Literal, Union, Optional, List, Dict, Annotated
from pydantic import ValidationError, BaseModel, field_validator, model_validator, Field, ConfigDict
from datetime import datetime
from feelpp.benchmarking.dashboardRenderer.plugins.figures.schemas.plot import Plot


class ReportNode(BaseModel):
    type:str


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

class JsonReportSchema(BaseModel):
    title: Optional[str] = "Report"
    datetime: Optional[str] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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