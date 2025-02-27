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

    def createCsvs(self,df):
        """Creates the corresponding csv strings for the figure
        Args:
            df (pd.DataFrame). The master dataframe containing all reframe test data
        Returns:
            list[dict[str,str]]: A list of dictionaries containing the csv strings and their corresponding titles.
            Schema: [{"title":str, "data":str}]
        """
        df = self.transformation_strategy.calculate(df)
        df = self.renameColumns(df)
        if isinstance(df.index,MultiIndex):
            return [{"title":key, "data":df.xs(key, level=0).to_csv()} for key in df.index.levels[0]]
        else:
            return [{"title":self.config.title, "data":df.to_csv()}]

    def createFigure(self,df, **args):
        """ Creates a figure from the master dataframe
        Args:
            df (pd.DataFrame). The master dataframe containing all reframe test data
        Returns:
            go.Figure: Plotly figure corresponding to the grouped Bar type
        """
        df = self.transformation_strategy.calculate(df)
        df = self.renameColumns(df)
        if isinstance(df.index,MultiIndex):
            figure = self.createMultiindexFigure(df, **args)
        else:
            figure = self.createSimpleFigure(df, **args)

        return figure

    def renameColumns(self,df):
        if self.config.variables and self.config.names:
            assert len(self.config.variables) == len(self.config.names)
            df = df.rename(columns = {var:name for var,name in zip(self.config.variables,self.config.names)})

        return df

class CompositeFigure:
    def createFigure(self, df):
        return self.plotly_figure.createFigure(df)

    def createTex(self, df):
        if self.tikz_figure is not None:
            return self.tikz_figure.createFigure(df)
        else:
            print("Warning: Tikz figure not implemented for this plot type")
            return None

    def createCsvs(self,df):
        return self.plotly_figure.createCsvs(df)

    def createFigureHtml(self,df):
        return self.plotly_figure.createHtml(df)