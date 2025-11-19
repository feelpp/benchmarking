from feelpp.benchmarking.dashboardRenderer.plugins.json2adoc.schemas.jsonReport import JsonReportSchema
from feelpp.benchmarking.dashboardRenderer.plugins.figures.controller import Controller as FigureController

class Controller:

    def __init__( self, config) -> None:
        self.config = JsonReportSchema.model_validate(config)

    def generateMetadata(self):
        metadata = []
        for meta_key,meta_value in self.config.metadata.model_dump().items():
            if meta_value:
                metadata.append(f":{meta_key.replace('_','-')}: {meta_value}")
        return "\n".join(metadata)

    def generateReport(self) -> str:
        return self.config.content