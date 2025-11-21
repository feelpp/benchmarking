import json, os, warnings
import pandas as pd

from feelpp.benchmarking.json_report.schemas.jsonReport import JsonReportSchema
from feelpp.benchmarking.dashboardRenderer.renderer import TemplateRenderer

class Json2AdocRenderer:
    def __init__(self, report_filepath: str, output_format:str = "adoc") -> None:
        self.report: JsonReportSchema = self.loadReport(report_filepath)
        self.renderer: TemplateRenderer = self.initRenderer(output_format)
        self.data:dict = self.loadReportData()

    def loadReport( self, report_filepath: str ) -> JsonReportSchema:
        if not os.path.exists( report_filepath ):
            raise FileNotFoundError(f"Report file '{report_filepath}' does not exist.")

        with open( report_filepath, "r" ) as f:
            data = json.load(f)

        return JsonReportSchema.model_validate( data, context={"report_filepath":report_filepath} )

    def initRenderer( self, output_format:str ) -> TemplateRenderer:
        template_filename = None
        if output_format == "adoc":
            template_filename = "report.adoc.j2"
        #TODO: add more formats here (latex,html,...)
        else:
            raise ValueError(f"Output format '{output_format}' not supported.")

        return TemplateRenderer( os.path.join(os.path.dirname(__file__),"templates"), template_filename)


    def loadReportData( self ):
        if not hasattr(self,"report"):
            raise RuntimeError("Report must be loaded before loading data files.")

        data = {}
        for d in self.report.data:
            filedata = None
            with open( d.filepath, "r" ) as f:
                if d.format == "json":
                    filedata = json.load(f)
                elif d.format == "csv":
                    filedata = pd.read_csv(f)
                elif d.format == "raw":
                    filedata = f.read()
                else:
                    warnings.warn(f"Data file format '{d.format}' not recognized. Skipping data file '{d.filepath}'")

            if d.preprocessor:
                filedata = d.preprocessor.apply(filedata)

            data[d.name] = filedata

        return data

    def render(self, output_filepath: str ) -> None:

        self.renderer.render( output_filepath, dict(report=self.report, report_data = self.data) )
