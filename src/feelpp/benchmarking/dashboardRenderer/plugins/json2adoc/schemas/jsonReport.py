from typing import Literal, Union, Optional, List, Dict, Annotated
from pydantic import ValidationError, BaseModel, field_validator, model_validator, Field, ConfigDict
from datetime import datetime
from feelpp.benchmarking.dashboardRenderer.plugins.figures.schemas.plot import Plot



class Metadata(BaseModel):
    model_config = ConfigDict( extra='allow' )


class ReportNode(BaseModel):
    type:str


class TextNode(ReportNode):
    type:Literal["text"]
    text: str

class PlotNode(ReportNode):
    type: Literal["plot"]
    plot: Plot

Node = Union[TextNode, "SectionNode", PlotNode]

class SectionNode(ReportNode):
    type:Literal["section"]
    title:str
    content: List[Node]

class JsonReportSchema(BaseModel):
    metadata: Optional[Metadata] = Metadata()
    content: Optional[List[Annotated[Node, Field(discriminator="type")]]] = []

    @model_validator(mode="before")
    @classmethod
    def coerceListInput( cls, values ):
        if not values:
            return {"metadata": Metadata(), "content": []}

        if isinstance(values, list):
            content = []
            for item in values:
                try:
                    node = PlotNode.model_validate({"type":"plot", "plot":item})
                except ValidationError:
                    node = item
                content.append(node)
            return {"metadata": Metadata(), "content": content}
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