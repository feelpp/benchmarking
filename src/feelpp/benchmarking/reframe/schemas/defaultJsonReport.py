from pydantic import model_validator, ValidationError
from typing import List,Dict, Optional
from feelpp.benchmarking.json_report.figures.schemas.plot import Plot, PlotAxis
from feelpp.benchmarking.json_report.schemas.jsonReport import JsonReportSchema

class DefaultPlotYAxis(PlotAxis):
    parameter: Optional[str] = "value"
    label: Optional[str] = "Value"

class DefaultColorAxis(PlotAxis):
    parameter: Optional[str] = "perfvalue"
    label: Optional[str] = "Performance Variables"

class DefaultPlot(Plot):
    yaxis: DefaultPlotYAxis = DefaultPlotYAxis()
    color_axis: DefaultColorAxis = DefaultColorAxis()

class JsonReportSchemaWithDefaults(JsonReportSchema):
    data: List[Dict] = [
        { "name":"reframe_json", "filepath":"./reframe_report.json" },
        {
            "name":"reframe_df",
            "filepath":"./reframe_report.json",
            "preprocessor":"feelpp.benchmarking.report.plugins.reframeReport:runsToDfPreprocessor",
        },
        {
            "type":"DataTable",
            "name":"parameter_table",
            "filepath":"./reframe_report.json",
            "preprocessor":"feelpp.benchmarking.report.plugins.reframeReport:runsToDfPreprocessor",
            "table_options":{
                "computed_columns":{
                    "logs_link":"f'link:logs/{row[\"testcases.hashcode\"]}.html[Logs]'"
                },
                "group_by":{"columns":["testcases.hashcode"], "agg":"first"},
                "format":{
                    "testcases.time_total":"%.3f",
                    "result":{"pass": "🟢", "fail": "🔴"}
                }
            }
        }
    ]

    @model_validator(mode="before")
    @classmethod
    def applyDefaultPlots(cls, values):
        """
        Automatically merges JSON plot items with DefaultPlot.
        """

        if not values:
            return values

        if isinstance(values, list):
            new_content = []
            for item in values:
                try:
                    node = { "type": "plot", "ref":"reframe_df", "plot": DefaultPlot.model_validate(item) }
                except ValidationError:
                    node = item
                new_content.append(node)

            return {"contents": new_content}

        elif isinstance(values, dict):
            if "contents" in values and isinstance(values["contents"], list):
                new_content = []
                for item in values["contents"]:
                    if isinstance(item, dict) and item.get("type") == "plot":
                        item = {
                            "type": "plot",
                            "ref":"reframe_df",
                            "plot": DefaultPlot.model_validate(item["plot"])
                        }
                    elif isinstance(item, dict) and item.get("type") == "section":
                        item = cls.applyDefaultPlots(item)
                    new_content.append(item)

                values["contents"] = new_content

            return values

        else:
            raise TypeError(f"Expected dict or list at root, got {type(values)}")


    @model_validator(mode="after")
    def setDefaultTitle(self):
        if self.title is None:
            self.title = f"{self.datetime}"

        return self

