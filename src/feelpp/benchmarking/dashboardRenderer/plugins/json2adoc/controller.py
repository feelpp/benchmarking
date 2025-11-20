from feelpp.benchmarking.dashboardRenderer.plugins.json2adoc.schemas.jsonReport import JsonReportSchema
from feelpp.benchmarking.dashboardRenderer.plugins.figures.controller import Controller as FigureController

class Controller:

    def __init__( self, config ) -> None:
        if config:
            self.config = JsonReportSchema.model_validate(config)
        else:
            self.config = JsonReportSchema.model_validate({})

    def generateReport(self) -> str:
        return self.config.content