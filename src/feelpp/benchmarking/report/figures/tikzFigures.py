from feelpp.benchmarking.report.renderer import Renderer

from feelpp.benchmarking.report.figures.base import Figure

class TikzFigure(Figure):
    """Base class for Tikz figures"""
    def __init__(self,plot_config, transformation_strategy, renderer_filename):
        super().__init__(plot_config, transformation_strategy)
        self.template_dirpath = "./src/feelpp/benchmarking/report/figures/templates/tikz/" #TODO: DO NOT HARDCODE PATHS

        self.renderer = Renderer(self.template_dirpath,renderer_filename)


    def createMultiindexFigure(self, df, **args):
        return self.renderer.template.render(
            xaxis = self.config.xaxis,
            yaxis = self.config.yaxis,
            caption = self.config.title,
            variables = df.columns.to_list(),
            names = self.config.names or df.columns.to_list(),
            secondary_axis = self.config.secondary_axis,
            anim_dimension_values = [str(dim) for dim in df.index.get_level_values(self.config.secondary_axis.parameter).unique().values],
            csv_datasets = [df.xs(dim,level=self.config.secondary_axis.parameter,axis=0).to_csv(sep="\t") for dim in df.index.get_level_values(self.config.secondary_axis.parameter).unique().values],
            **args
        )

    def createSimpleFigure(self, df, **args):
        return self.renderer.template.render(
            xaxis = self.config.xaxis,
            yaxis = self.config.yaxis,
            caption = self.config.title,
            variables = df.columns.to_list(),
            names = self.config.names or df.columns.to_list(),
            csv_datasets = [df.to_csv(sep="\t")],
            **args
        )


class TikzScatterFigure(TikzFigure):
    def __init__(self, plot_config, transformation_strategy, fill_lines = []):
        super().__init__(plot_config, transformation_strategy, "scatterChart.tex.j2")
        self.fill_lines = fill_lines

    def createFigure(self, df):
        return super().createFigure(df, fill_lines = self.fill_lines)

class TikzTableFigure(TikzFigure):
    def __init__(self, plot_config, transformation_strategy):
        super().__init__(plot_config, transformation_strategy, "tableChart.tex.j2")

class TikzStackedBarFigure(TikzFigure):
    def __init__(self, plot_config, transformation_strategy):
        super().__init__(plot_config, transformation_strategy, "stackedBarChart.tex.j2")

class TikzGroupedBarFigure(TikzFigure):
    def __init__(self, plot_config, transformation_strategy):
        super().__init__(plot_config, transformation_strategy, "groupedBarChart.tex.j2")
