import os, zipfile
from typing import List, Dict, Union
import pandas as pd
from uuid import uuid4

from feelpp.benchmarking.json_report.figures.transformationFactory import TransformationFactory
from feelpp.benchmarking.json_report.figures.figureFactory import FigureFactory
from feelpp.benchmarking.json_report.figures.schemas.plot import Plot

class Controller:
    def __init__(self, data:pd.DataFrame, plot_config: Union[Dict,Plot], report_uuid:str = None):
        """
        """
        self.report_uuid = report_uuid
        self.id = uuid4().hex
        if not isinstance(data,pd.DataFrame):
            raise NotImplementedError(f"Data type {type(data)} not supported for Figures")

        if isinstance(plot_config,Plot):
            self.plot_config = plot_config
        elif isinstance(plot_config,Dict):
            self.plot_config = Plot(**plot_config)
        else:
            raise TypeError(f"plot_config must be a Dict or a Plot model, got {type(plot_config)}")

        self.data = data #TransformationFactory.create(self.plot_config).calculate(data)

        self.figures = FigureFactory.create(self.plot_config)


    def dumpFigureJsons(self,outdir:str = ".") -> str:
        """ Returns the path relative to outdir """
        plotly_figs = [fig.createFigure(self.data) for fig in self.figures]
        filepaths = []
        for plotly_fig,plot_type in zip(plotly_figs,self.plot_config.plot_types):
            if self.report_uuid:
                fig_relpath = os.path.join(self.report_uuid,self.id,f"{plot_type}.json")
            else:
                fig_relpath = os.path.join(self.id,f"{plot_type}.json")

            filepath = os.path.join(outdir,fig_relpath)

            os.makedirs(os.path.dirname(filepath),exist_ok=True)

            with open(filepath,"w") as f:
                f.write(plotly_fig.to_json())

            filepaths.append(fig_relpath)
        return filepaths


    def dumpFigureCsvs(self, outdir:str = ".") -> str:
        """ Returns the path relative to outdir """
        filepaths = []
        for figure,plot_type in zip(self.figures,self.plot_config.plot_types):
            if self.report_uuid:
                fig_relpath = os.path.join(self.report_uuid,self.id,f"{plot_type}.zip")
            else:
                fig_relpath = os.path.join(self.id,f"{plot_type}.zip")

            filepath = os.path.join(outdir,fig_relpath)

            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            csvs = figure.createCsvs(self.data)
            with zipfile.ZipFile( file=filepath, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zip_archive:
                for csv in csvs:
                    zip_archive.writestr(zinfo_or_arcname=f"{csv['title']}.csv",data=csv['data'])

            filepaths.append(fig_relpath)
        return filepaths

    # def generateAll(self):
    #     if self.df is None or self.df.empty:
    #         return []
    #     return [
    #         self.generateFigure(figure,plot_config.plot_types)
    #         for figure,plot_config in zip(self.figures,self.plots_config)
    #     ]

    # def generateFigure(self,figure,plot_types):
    #     return {
    #         "plot_types": plot_types,
    #         "subfigures": [self.generateSubfigure(subfigure) for subfigure in figure]
    #     }

    # def generateSubfigure(self, subfigure):
    #     return {
    #         "exports": [
    #             { "display_text":"CSV", "data":[
    #                 { "format":"csv", "prefix":"data","content":subfigure.createCsvs(self.df)}
    #             ]},
    #             { "display_text":"LaTeX", "data":[
    #                 {"format":"tex","content":[{ "data":subfigure.createTex(self.df), "title":"figures" }]},
    #                 {"format":"csv","content":subfigure.createCsvs(self.df)}

    #             ]},
    #         ],
    #         "html": subfigure.createFigureHtml(self.df)
    #     }