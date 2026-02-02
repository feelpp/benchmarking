import os, zipfile
from typing import List, Dict, Union
import pandas as pd
from uuid import uuid4

from feelpp.benchmarking.json_report.figures.transformationFactory import TransformationFactory
from feelpp.benchmarking.json_report.figures.plotly.figureFactory import FigureFactory as PlotlyFigureFactory
from feelpp.benchmarking.json_report.figures.tikz.figureFactory import FigureFactory as TikzFigureFactory
from feelpp.benchmarking.json_report.figures.schemas.plot import Plot

class Controller:
    """
        One semantic figure:
        - same data
        - multiple transformations
        - multiple views
        - multiple exports
    """
    def __init__(self, data:pd.DataFrame, plot_config: Union[Dict,Plot], report_uuid:str = None):
        self.report_uuid = report_uuid
        self.id = uuid4().hex
        if not isinstance(data,pd.DataFrame):
            raise NotImplementedError(f"Data type {type(data)} not supported for Figures")
        self.plot_config = self.coercePlotConfig(plot_config)

        #TODO: allow multiple transformations in the future
        self.transformed = { self.plot_config.transformation : TransformationFactory.create(self.plot_config).calculate(data) }

        self.figure_views = {
            plot_type : {
                "plotly": PlotlyFigureFactory.create(plot_type,plot_config=self.plot_config),
                "latex": TikzFigureFactory.create(plot_type,plot_config=self.plot_config),
            }
            for plot_type in self.plot_config.plot_types
        }

    def coercePlotConfig(self, config):
        if isinstance(config,Plot):
            plot_config = config
        elif isinstance(config,Dict):
            plot_config = Plot(**config)
        else:
            raise TypeError(f"plot_config must be a Dict or a Plot model, got {type(config)}")
        return plot_config


    def renderFigure(self, plot_type, backend, transformation, data_dir = "." ):
        figure = self.figure_views[plot_type][backend]
        if not figure:
            return None
        return figure.createFigure(self.transformed[transformation],data_dir)

    def exportFigureData(self, plot_type, backend, transformation, formats=["csv"], outdir:str = ".") -> list[dict[str,str]]:
        figure = self.figure_views[plot_type][backend]
        if not figure:
            return None
        if self.report_uuid:
            relpath = os.path.join(self.report_uuid,self.id,f"{plot_type}")
        else:
            relpath = os.path.join(self.id,f"{plot_type}")

        filepath = os.path.join(outdir,relpath)

        os.makedirs(os.path.dirname(filepath),exist_ok=True)

        exported_paths = {}
        if "json" in formats:
            with open(f"{filepath}.json","w") as f:
                f.write(figure.createJson(self.transformed[transformation]))

            exported_paths["json"] = f"{relpath}.json"
        if "csv" in formats:
            os.mkdir(filepath)
            csvs = figure.createCsvs(self.transformed[transformation])
            for csv in csvs:
                csv_fn = os.path.join(filepath,f"{csv['title']}.csv")
                with open(csv_fn,"w") as f:
                    f.write(csv['data'])
            exported_paths["csv"] = relpath

        if "zip_csv" in formats:
            csvs = figure.createCsvs( self.transformed[transformation] )
            with zipfile.ZipFile( file=f"{filepath}.zip", mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zip_archive:
                for csv in csvs:
                    zip_archive.writestr(zinfo_or_arcname=f"{csv['title']}.csv",data=csv['data'])
            exported_paths["zip_csv"] = f"{relpath}.zip"

        return exported_paths