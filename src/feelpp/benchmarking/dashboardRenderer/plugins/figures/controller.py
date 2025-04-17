from feelpp.benchmarking.dashboardRenderer.plugins.figures.figureFactory import FigureFactory
from feelpp.benchmarking.dashboardRenderer.plugins.figures.schemas.plot import Plot

class Controller:
    """ Controller component , it orchestrates the model with the view"""
    def __init__(self, df, plots_config):
        """
        Args:
            model (pd.DataFrame): The atomic report model component
            view (AtomicReportView): The atomic report view component
        """
        self.df = df
        self.plots_config = [Plot(**d) for d in plots_config]
        self.figures = [FigureFactory.create(plot_config) for plot_config in self.plots_config]

    def generateAll(self):
        if self.df.empty:
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