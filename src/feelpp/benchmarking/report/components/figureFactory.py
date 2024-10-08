import plotly.graph_objects as go
import pandas as pd
from numpy import float64 as float64

from feelpp.benchmarking.report.components.strategies import StrategyFactory

class Figure:
    """ Abstract class for a figure """
    def __init__(self,plot_config,transformation_strategy):
        self.config = plot_config
        self.transformation_strategy = transformation_strategy

    def createFigure(self,df):
        """ Pure virtual method to create a figure
        Args:
            df (pd.DataFrame). The transformed dataframe
        """
        raise NotImplementedError("Not to be called directly.")


class ScatterFigure(Figure):
    """ Concrete Figure class for scatter figures """
    def __init__(self, plot_config,transformation_strategy):
        super().__init__(plot_config,transformation_strategy)

    def createAnimation(self,df):
        """ Creates a plotly figure from a multiIndex dataframe
        Args:
            df (pd.DataFrame). The transformed dataframe (must be multiindex)
        Returns:
            go.Figure: Scatter animation where the animation axis corresponds to a specified parameter
        """
        frames = []

        anim_dimension_values = df.index.get_level_values(self.config.animation_axis.parameter).unique().values

        range_epsilon= 0.01

        ranges=[]

        for j,dim in enumerate(anim_dimension_values):
            partial_df = df.xs(dim,level=self.config.animation_axis.parameter,axis=0)
            frames.append([
                go.Scatter(
                    x = partial_df.index,
                    y = partial_df.loc[:,col],
                    name=name
                )
                for name,col in zip(self.config.names,partial_df.columns)
            ])
            ranges.append([
                partial_df.min().min() - partial_df.min().min()*range_epsilon,
                partial_df.max().max() + partial_df.min().min()*range_epsilon
            ])

        fig = go.Figure(
            data = frames[0],
            frames = [
                go.Frame(
                    data = f,
                    name=f"frame_{i}",
                    layout=dict(
                        yaxis=dict(range = ranges[i])
                    )
                )
                for i,f in enumerate(frames)],
            layout=go.Layout(
                yaxis=dict(range = ranges[0],title=self.config.yaxis.label),
                xaxis=dict(title=self.config.xaxis.label),
                title=self.config.title,
                sliders=[dict(
                    active=0, currentvalue=dict(prefix=f"{self.config.animation_axis.label} = "), transition = dict(duration= 0),
                    steps=[dict(label=f"{h}",method="animate",args=[[f"frame_{k}"],dict(mode="immediate",frame=dict(duration=0, redraw=True))]) for k,h in enumerate(anim_dimension_values)],
                )]
            )
        )

        return fig

    def createSimple(self,df):
        """ Creates a plotly figure from a given dataframe
        Args:
            df (pd.DataFrame). The transformed dataframe
        Returns:
            go.Figure: Scatter plot
        """
        return go.Figure(
            data = [
                go.Scatter( x = df.index, y = df.loc[:,col], name = name )
                for name,col in zip(self.config.names,df.columns)
            ],
            layout=go.Layout(
                title=self.config.title,
                xaxis=dict( title = self.config.xaxis.label ),
                yaxis=dict( title = self.config.yaxis.label )
            )
        )

    def createFigure(self,df):
        """ Creates a scatter plot from the master dataframe
        Args:
            df (pd.DataFrame). The master dataframe containing all reframe test data
        Returns:
            go.Figure: Plotly figure corresponding to the Scatter type
        """
        df = self.transformation_strategy.calculate(df)

        if isinstance(df.index,pd.MultiIndex):
            return self.createAnimation(df)
        else:
            return self.createSimple(df)


class TableFigure(Figure):
    """ Concrete Figure class for scatter figures """
    def __init__(self, plot_config, transformation_strategy):
        super().__init__(plot_config, transformation_strategy)
        self.precision = 3

    def createMultiindexTable(self,df):
        """ Creates a plotly table from a multiindex dataframe
            Args:
                df (pd.DataFrame). The transformed dataframe (must be multiindex)
            Returns:
                go.Figure. Containing a table trace for  multiindex dataframe
        """
        return go.Figure(
            go.Table(
                header=dict(values= df.index.names + df.columns.tolist()),
                cells=dict(
                    values=[df.index.get_level_values(i) for i in range(len(df.index.names))] + [df[col] for col in df.columns],
                    format=[f'.{self.precision}' if t == float64 else '' for t in [df.index.dtype] + df.dtypes.values.tolist()]
                )
            )
        )

    def createSimple(self,df):
        """ Creates a simple plotly table from a dataframe
            Args:
                df (pd.DataFrame). The transformed dataframe
            Returns:
                go.Figure. Containing a table trace
        """
        return go.Figure(
            go.Table(
                header=dict(values= [df.index.name] + df.columns.tolist()),
                cells=dict(
                    values= [df.index.values.tolist()] + [df[col] for col in df.columns],
                    format=[f'.{self.precision}' if t == float64 else '' for t in [df.index.dtype] + df.dtypes.values.tolist()]
                )
            )
        )


    def createFigure(self,df):
        """ Creates a table figure the master dataframe
        Args:
            df (pd.DataFrame). The master dataframe containing all reframe test data
        Returns:
            go.Figure: Plotly figure corresponding to the Table type
        """
        df = self.transformation_strategy.calculate(df)

        if isinstance(df,pd.MultiIndex):
            return self.createMultiindex(df)
        else:
            return self.createSimple(df)


class FigureFactory:
    """ Factory class to dispatch concrete figure elements"""
    @staticmethod
    def create(plot_config):
        """ Creates a concrete figure element
        Args:
            plot_config (Plot). Pydantic object with the plot configuration information
        """
        strategy = StrategyFactory.create(plot_config)
        figures = []
        for plot_type in plot_config.plot_types:
            match plot_type:
                case "scatter":
                    figures.append(ScatterFigure(plot_config,strategy))
                case "table":
                    figures.append(TableFigure(plot_config,strategy))
                case _:
                    raise NotImplementedError

        return figures