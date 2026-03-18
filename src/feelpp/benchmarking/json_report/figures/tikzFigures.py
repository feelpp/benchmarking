from jinja2 import Environment, FileSystemLoader
from feelpp.benchmarking.json_report.figures.base import Figure

from pathlib import Path

class Renderer:
    def __init__(self, template_paths, template_filename) -> None:
        self.env = Environment(loader=FileSystemLoader(template_paths), trim_blocks=True, lstrip_blocks=True)
        self.env.filters["inttouniquestr"] = self.intToUniqueStr
        self.env.globals.update(zip=zip)
        self.template = self.env.get_template(template_filename)

    def render(self, output_filepath, data={}):
        """ Render the JSON file to an AsciiDoc file using a Jinja2 template and the given data"""
        with open(output_filepath, 'w') as f:
            f.write(self.template.render(data))

    @staticmethod
    def intToUniqueStr(n):
        s = []
        while n:
            n, r = divmod(n - 1, 26)
            s.append(chr(65 + r))
        return "".join(reversed(s))


class TikzFigure(Figure):
    """Base class for Tikz figures"""
    def __init__(self,plot_config, transformation_strategy, renderer_filename):
        super().__init__(plot_config, transformation_strategy)
        self.template_dirpath = f"{Path(__file__).resolve().parent}/templates/tikz/"

        self.renderer = Renderer(self.template_dirpath,renderer_filename)
        self.xcolors = ["red","green","blue","magenta","yellow","black","gray","white","darkgray","lightgray","olive","orange","pink","purple","teal","violet","cyan","brown","lime"]


    def createMultiindexFigure(self, df, **args):
        """ Creates a latex tikz (pgfplots) figure from a multiIndex dataframe
        Args:
            df (pd.DataFrame). The transformed dataframe (must be multiindex)
        Returns:
            str: latex file content where containing multiple pgfplots figures, for each value of secondary axis
        """
        secondary_axis = self.transformation_strategy.dimensions["secondary_axis"].parameter
        anim_dim_values = df.index.get_level_values(secondary_axis).unique().values
        return self.renderer.template.render(
            xaxis = self.config.xaxis,
            yaxis = self.config.yaxis,
            caption = self.config.title,
            variables = df.columns.to_list(),
            secondary_axis = self.config.secondary_axis,
            anim_dimension_values = [str(dim) for dim in anim_dim_values],
            csv_filenames = [f"{dim}.csv" for dim in anim_dim_values],
            **args
        )

    def createSimpleFigure(self, df, **args):
        """ Creates a latex tikz (pgfplots) figure from a given dataframe
        Args:
            df (pd.DataFrame). The transformed dataframe
        Returns:
            str: latex file content containing the pgfplots figure
        """
        return self.renderer.template.render(
            xaxis = self.config.xaxis,
            yaxis = self.config.yaxis,
            caption = self.config.title,
            variables = df.columns.to_list(),
            csv_filenames = [f"{self.config.title}.csv"],
            **args
        )


class TikzScatterFigure(TikzFigure):
    """ Concrete Figure class for pgfplots scatter figure"""
    def __init__(self, plot_config, transformation_strategy, fill_lines = []):
        super().__init__(plot_config, transformation_strategy, "scatterChart.tex.j2")
        self.fill_lines = fill_lines

    def createFigure(self, df):
        return super().createFigure(df, fill_lines = self.fill_lines)

class TikzTableFigure(TikzFigure):
    """ Concrete Figure class for pgfplots table"""
    def __init__(self, plot_config, transformation_strategy):
        super().__init__(plot_config, transformation_strategy, "tableChart.tex.j2")

class TikzStackedBarFigure(TikzFigure):
    """ Concrete Figure class for pgfplots stacked bar figure"""
    def __init__(self, plot_config, transformation_strategy):
        super().__init__(plot_config, transformation_strategy, "stackedBarChart.tex.j2")

    def createFigure(self,df):
        return super().createFigure(df, colors=self.xcolors[:len(df.columns)])

class TikzGroupedBarFigure(TikzFigure):
    """ Concrete Figure class for pgfplots grouped bar figure"""
    def __init__(self, plot_config, transformation_strategy):
        super().__init__(plot_config, transformation_strategy, "groupedBarChart.tex.j2")
