from feelpp.benchmarking.dashboardRenderer.plugins.figures.figureFactory import FigureFactory
from feelpp.benchmarking.dashboardRenderer.plugins.figures.schemas.plot import Plot
from typing import List, Dict, Union

class Controller:
    """ Controller component , it orchestrates the model with the view"""
    def __init__(self, df, plots_config: Union[List[Dict],Dict,Plot,List[Plot]]):
        """
        Args:
            model (pd.DataFrame): The atomic report model component
            view (AtomicReportView): The atomic report view component
        """
        self.df = df
        if isinstance(plots_config,Plot):
            self.plots_config = [plots_config]
        elif isinstance(plots_config,Dict):
            self.plots_config = [Plot(**plots_config)]
        elif isinstance(plots_config,List):
            if all(isinstance(d,Plot) for d in plots_config):
                self.plots_config = plots_config
            else:
                self.plots_config = [Plot(**d) for d in plots_config]
        else:
            raise TypeError(f"plots_config must be a Dict or List of Dicts, got {type(plots_config)}")
        self.figures = [FigureFactory.create(plot_config) for plot_config in self.plots_config]

    def generateAll(self):
        if self.df is None or self.df.empty:
            return []
        return [
            self.generateFigure(figure,plot_config.plot_types)
            for figure,plot_config in zip(self.figures,self.plots_config)
        ]

    def generateFigure(self,figure,plot_types):
        return {
            "plot_types": plot_types,
            "subfigures": [self.generateSubfigure(subfigure) for subfigure in figure]
        }

    def generateSubfigure(self, subfigure):
        return {
            "exports": [
                { "display_text":"CSV", "data":[
                    { "format":"csv", "prefix":"data","content":subfigure.createCsvs(self.df)}
                ]},
                { "display_text":"LaTeX", "data":[
                    {"format":"tex","content":[{ "data":subfigure.createTex(self.df), "title":"figures" }]},
                    {"format":"csv","content":subfigure.createCsvs(self.df)}

                ]},
            ],
            "html": subfigure.createFigureHtml(self.df)
        }