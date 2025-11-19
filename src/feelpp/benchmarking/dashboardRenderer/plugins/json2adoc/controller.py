from feelpp.benchmarking.dashboardRenderer.plugins.json2adoc.schemas.jsonReport import JsonReportSchema
from feelpp.benchmarking.dashboardRenderer.plugins.figures.controller import Controller as FigureController

class Controller:

    def __init__( self, config ) -> None:
        self.config = JsonReportSchema.model_validate(config)

    def generateReport(self) -> str:
        return self.config.content