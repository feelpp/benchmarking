from feelpp.benchmarking.report.renderer import Renderer

from feelpp.benchmarking.report.figures.base import Figure

class TikzFigure(Figure):
    """Base class for Tikz figures"""
    def __init__(self,plot_config, transformation_strategy, renderer_filename):
        super().__init__(plot_config, transformation_strategy)
        self.template_dirpath = "./src/feelpp/benchmarking/report/figures/templates/tikz/" #TODO: DO NOT HARDCODE PATHS

        self.renderer = Renderer(self.template_dirpath,renderer_filename)
        self.xcolors = ["red","green","blue","magenta","yellow","black","gray","white","darkgray","lightgray","olive","orange","pink","purple","teal","violet","cyan","brown","lime"]

    def parseSpecialCharacters(self, value, replace_map = {"_":"-"}):
        """ Replaces certain characters with other ones depending on the replace_map
        Args:
            value (str): String to parse
            replace_map (dict[str,str]): Characters to replace and their respective replace values
        Returns:
            str: Parsed string with characters replaced
        """
        parsed_value = str(value)
        for char,replace_char in replace_map.items():
            parsed_value = parsed_value.replace(char,replace_char)
        return parsed_value

    def createMultiindexFigure(self, df, **args):
        """ Creates a latex tikz (pgfplots) figure from a multiIndex dataframe
        Args:
            df (pd.DataFrame). The transformed dataframe (must be multiindex)
        Returns:
            str: latex file content where containing multiple pgfplots figures, for each value of secondary axis
        """
        return self.parseSpecialCharacters(self.renderer.template.render(
            xaxis = self.config.xaxis,
            yaxis = self.config.yaxis,
            caption = self.config.title,
            variables = df.columns.to_list(),
            names = self.config.names or df.columns.to_list(),
            secondary_axis = self.config.secondary_axis,
            anim_dimension_values = [str(dim) for dim in df.index.get_level_values(self.config.secondary_axis.parameter).unique().values],
            csv_datasets = [df.xs(dim,level=self.config.secondary_axis.parameter,axis=0).to_csv(sep="\t") for dim in df.index.get_level_values(self.config.secondary_axis.parameter).unique().values],
            **args
        ))

    def createSimpleFigure(self, df, **args):
        """ Creates a latex tikz (pgfplots) figure from a given dataframe
        Args:
            df (pd.DataFrame). The transformed dataframe
        Returns:
            str: latex file content containing the pgfplots figure
        """
        return self.parseSpecialCharacters(self.renderer.template.render(
            xaxis = self.config.xaxis,
            yaxis = self.config.yaxis,
            caption = self.config.title,
            variables = df.columns.to_list(),
            names = self.config.names or df.columns.to_list(),
            csv_datasets = [df.to_csv(sep="\t")],
            **args
        ))


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
