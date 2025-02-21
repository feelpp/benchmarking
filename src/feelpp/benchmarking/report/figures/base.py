from pandas import MultiIndex

class Figure:
    def __init__(self,plot_config,transformation_strategy):
        self.config = plot_config
        self.transformation_strategy = transformation_strategy

    def getIdealRange(self,df):
        """ Computes the [(min - eps), (max+eps)] interval for optimal y-axis display
        Args:
            - df (pd.DataFrame): The dataframe for which the interval should be computed
        Returns list[float, float]: The  [(min - eps), (max+eps)] interval
        """
        range_epsilon= 0.01
        return [ df.min().min() - df.min().min()*range_epsilon, df.max().max() + df.min().min()*range_epsilon ]

    def createMultiindexFigure(self,df):
        raise NotImplementedError("Pure virtual function. Not to be called from the base class")

    def createSimpleFigure(self,df):
        raise NotImplementedError("Pure virtual function. Not to be called from the base class")

    def createCsv(self,df):
        return self.transformation_strategy.calculate(df).to_csv()

    def createFigure(self,df, **args):
        """ Creates a figure from the master dataframe
        Args:
            df (pd.DataFrame). The master dataframe containing all reframe test data
        Returns:
            go.Figure: Plotly figure corresponding to the grouped Bar type
        """
        df = self.transformation_strategy.calculate(df)

        if isinstance(df.index,MultiIndex):
            figure = self.createMultiindexFigure(df, **args)
        else:
            figure = self.createSimpleFigure(df, **args)

        return figure


class CompositeFigure:
    def createFigure(self, df):
        return self.plotly_figure.createFigure(df)

    def createTex(self, df):
        if self.tikz_figure is not None:
            return self.tikz_figure.createFigure(df)
        else:
            print("Warning: Tikz figure not implemented for this plot type")
            return None

    def createCsv(self,df):
        return self.plotly_figure.createCsv(df)

    def createFigureHtml(self,df):
        return self.plotly_figure.createHtml(df)