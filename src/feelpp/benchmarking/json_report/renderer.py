import json, os, warnings
import pandas as pd

from feelpp.benchmarking.json_report.schemas.jsonReport import JsonReportSchema
from feelpp.benchmarking.dashboardRenderer.renderer import TemplateRenderer
from feelpp.benchmarking.json_report.figures.controller import Controller as FiguresController
from feelpp.benchmarking.json_report.tables.controller import Controller as TableController
from feelpp.benchmarking.json_report.text.controller import Controller as TextController
from feelpp.benchmarking.json_report.dataLoader import DataFieldParser, DataReferenceDependencyGraph

class JsonReportController:
    def __init__(self, report_filepath: str, output_format:str = "adoc") -> None:
        self.report_filepath:str = report_filepath
        self.output_format:str = output_format
        self.report: JsonReportSchema = self.loadReport(report_filepath)
        self.renderer: TemplateRenderer = self.initRenderer()

        self.exposed:dict = dict()
        self.data:dict = self.loadReportData()

    def loadReport( self, report_filepath: str ) -> JsonReportSchema:
        if not os.path.exists( report_filepath ):
            warnings.warn(f"Report file '{report_filepath}' does not exist.")
            return JsonReportSchema()

        with open( report_filepath, "r" ) as f:
            data = json.load(f)

        return JsonReportSchema.model_validate( data, context={"report_filepath":report_filepath} )

    def getTemplatePath( self ):
        template_filename = None
        if self.output_format == "adoc":
            template_filename = "json2adoc_report.adoc.j2"
        #TODO: add more formats here (latex,html,...)
        else:
            raise ValueError(f"Output format '{self.output_format}' not supported.")
        return os.path.join(os.path.dirname(__file__),"templates"), template_filename


    def initRenderer( self) -> TemplateRenderer:
        template_path, template_filename = self.getTemplatePath( )
        renderer = TemplateRenderer( template_paths=template_path, template_filename=template_filename )
        renderer.env.globals.update( {
            "FiguresController":FiguresController,
            "TableController":TableController,
            "TextController":TextController
        } )

        return renderer

    def loadReportData( self ):
        if not hasattr(self,"report"):
            raise RuntimeError("Report must be loaded before loading data files.")

        data = {}
        data_graph = DataReferenceDependencyGraph(self.report.data)
        for field_name, field in data_graph.data_fields.items():
            filedata = {field_name : data_graph.resolve(field_name)}
            data[field_name] = filedata

            if field.expose:
                self.exposed[field.expose] = filedata

        return data

    def render(self, output_dirpath: str, output_filename:str = None ) -> str:
        if not os.path.exists( output_dirpath ):
            os.makedirs( output_dirpath )

        if output_filename is None:
            output_filename = self.report_filepath.replace('.json', f'.{self.output_format}')

        output_filepath = os.path.join( output_dirpath, os.path.basename(output_filename) )

        self.renderer.render( output_filepath, dict(report=self.report, report_data = self.data ))

        return os.path.abspath(output_filepath)