

class Controller:
    """ Controller component , it orchestrates the model with the view"""
    def __init__(self, model, view):
        """
        Args:
            model (AtomicReportModel): The atomic report model component
            view (AtomicReportView): The atomic report view component
        """
        self.model = model
        self.view = view

    def generateAll(self):
        return [
            self.generateFigure(figure,plot_config.plot_types)
            for figure,plot_config in zip(self.view.figures,self.view.plots_config)
        ]

    def generateFigure(self,figure,plot_types):
        return {
            "plot_types": plot_types,
            "subfigures": [self.generateSubfigure(subfigure) for subfigure in figure]
        }

    def generateSubfigure(self, subfigure):
        return {
            "exports": [
                { "display_text":"CSV", "filename":"data.csv", "data":subfigure.createCsv(self.model.master_df) },
                { "display_text":"LaTeX", "filename":"figure.tex", "data":subfigure.createTex(self.model.master_df) },
            ],
            "html": subfigure.createFigureHtml(self.model.master_df)
        }