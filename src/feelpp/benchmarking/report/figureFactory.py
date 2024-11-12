import plotly.graph_objects as go
import plotly.express as px
from pandas import MultiIndex
from numpy import float64 as float64

from feelpp.benchmarking.report.strategies import StrategyFactory

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
            go.Figure: Scatter animation where the secondary_ axis corresponds to a specified parameter
        """
        frames = []
        anim_dimension_values = df.index.get_level_values(self.config.secondary_axis.parameter).unique().values
        range_epsilon= 0.01

        ranges=[]

        for j,dim in enumerate(anim_dimension_values):
            frame_df = df.xs(dim,level=self.config.secondary_axis.parameter,axis=0)
            frames.append([
                go.Scatter(
                    x = frame_df.index,
                    y = frame_df.loc[:,col],
                    name=col
                )
                for col in frame_df.columns
            ])
            ranges.append([
                frame_df.min().min() - frame_df.min().min()*range_epsilon,
                frame_df.max().max() + frame_df.min().min()*range_epsilon
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
                    active=0, currentvalue=dict(prefix=f"{self.config.secondary_axis.label} = "), transition = dict(duration= 0),
                    steps=[dict(label=f"{h}",method="animate",args=[[f"frame_{k}"],dict(mode="immediate",frame=dict(duration=0, redraw=True))]) for k,h in enumerate(anim_dimension_values)],
                )],
                legend=dict(title=self.config.color_axis.label if self.config.color_axis else "")
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
                go.Scatter( x = df.index, y = df.loc[:,col], name = col )
                for col in df.columns
            ],
            layout=go.Layout(
                title=self.config.title,
                xaxis=dict( title = self.config.xaxis.label ),
                yaxis=dict( title = self.config.yaxis.label ),
                legend=dict(title=self.config.color_axis.label if self.config.color_axis else "")
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

        if isinstance(df.index,MultiIndex):
            return self.createAnimation(df)
        else:
            return self.createSimple(df)


class TableFigure(Figure):
    """ Concrete Figure class for scatter figures """
    def __init__(self, plot_config, transformation_strategy):
        super().__init__(plot_config, transformation_strategy)
        self.precision = 3

    def createMultiindex(self,df):
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

        if isinstance(df.index,MultiIndex):
            return self.createMultiindex(df)
        else:
            return self.createSimple(df)


class StackedBarFigure(Figure):
    """ Concrete Figure class for stacked bar charts"""
    def __init__(self, plot_config, transformation_strategy):
        super().__init__(plot_config, transformation_strategy)

    def createGrouped(self,df):
        """ Creates a stacked and grouped plotly bar chart from a multiindex dataframe
            Args:
                df (pd.DataFrame). The transformed dataframe (must be multiindex)
            Returns:
                go.Figure. Containing a stacked and grouped bar traces for a multiindex dataframe
        """
        fig = px.bar(
            df.reset_index().astype({
                self.config.secondary_axis.parameter:"str",
                self.config.xaxis.parameter:"str"
            }).rename(
                columns = {
                    self.config.xaxis.parameter:self.config.xaxis.label,
                    self.config.secondary_axis.parameter:self.config.secondary_axis.label
                },
            ),
            x=self.config.secondary_axis.label,
            y=df.columns,
            facet_col=self.config.xaxis.label,
        )
        fig.update_layout(
            yaxis=dict(title=self.config.yaxis.label),
            title = self.config.title,
            legend=dict(title=self.config.color_axis.label if self.config.color_axis else "")
        )
        return fig

    def createSimple(self,df):
        """ Creates a stacked plotly bar chart from a single indexed dataframe
            Args:
                df (pd.DataFrame). The transformed dataframe
            Returns:
                go.Figure. Containing a stacked bar traces.
        """
        return go.Figure(
            data = [
                go.Bar(x = df.index.astype(str), y = df.loc[:,col],name=col)
                for col in df.columns
            ],
            layout=go.Layout(
                barmode="stack",
                xaxis=dict(
                    title = self.config.xaxis.label
                ),
                yaxis=dict(
                    title = self.config.yaxis.label
                ),
                title = self.config.title,
                legend=dict(title=self.config.color_axis.label if self.config.color_axis else "")
            )
        )

    def createFigure(self,df):
        """ Creates a stacked bar figure from the master dataframe
        Args:
            df (pd.DataFrame). The master dataframe containing all reframe test data
        Returns:
            go.Figure: Plotly figure corresponding to the Stacked Bar type
        """
        df = self.transformation_strategy.calculate(df)

        if isinstance(df.index,MultiIndex):
            return self.createGrouped(df)
        else:
            return self.createSimple(df)

class GroupedBarFigure(Figure): #TODO: FACTOR animation and bar...
    def __init__(self, plot_config, transformation_strategy):
        super().__init__(plot_config, transformation_strategy)

    def createGrouped(self,df):
        frames = []
        anim_dimension_values = df.index.get_level_values(self.config.secondary_axis.parameter).unique().values
        range_epsilon= 0.01


        ranges=[]

        for j,dim in enumerate(anim_dimension_values):
            frame_df = df.xs(dim,level=self.config.secondary_axis.parameter,axis=0)
            frames.append([
                go.Bar(
                    x = frame_df.index.astype(str),
                    y = frame_df.loc[:,col],
                    name=col
                )
                for col in frame_df.columns
            ])
            ranges.append([
                frame_df.min().min() - frame_df.min().min()*range_epsilon,
                frame_df.max().max() + frame_df.min().min()*range_epsilon
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
                    active=0, currentvalue=dict(prefix=f"{self.config.secondary_axis.label} = "), transition = dict(duration= 0),
                    steps=[dict(label=f"{h}",method="animate",args=[[f"frame_{k}"],dict(mode="immediate",frame=dict(duration=0, redraw=True))]) for k,h in enumerate(anim_dimension_values)],
                )],
                legend=dict(title=self.config.color_axis.label if self.config.color_axis else "")
            )
        )

        return fig

    def createSimple(self,df):
        return go.Figure(
            data = [
                go.Bar(x = df.index.astype(str), y = df.loc[:,col],name=col)
                for col in df.columns
            ],
            layout=go.Layout(
                xaxis=dict(
                    title = self.config.xaxis.label
                ),
                yaxis=dict(
                    title = self.config.yaxis.label
                ),
                title = self.config.title,
                legend=dict(title=self.config.color_axis.label if self.config.color_axis else "")
            )
        )


    def createFigure(self,df):
        """ Creates a grouped bar figure from the master dataframe
        Args:
            df (pd.DataFrame). The master dataframe containing all reframe test data
        Returns:
            go.Figure: Plotly figure corresponding to the grouped Bar type
        """
        df = self.transformation_strategy.calculate(df)

        if isinstance(df.index,MultiIndex):
            return self.createGrouped(df)
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
            if plot_type ==  "scatter":
                figures.append(ScatterFigure(plot_config,strategy))
            elif plot_type == "table":
                figures.append(TableFigure(plot_config,strategy))
            elif plot_type == "stacked_bar":
                figures.append(StackedBarFigure(plot_config,strategy))
            elif plot_type == "grouped_bar":
                figures.append(GroupedBarFigure(plot_config,strategy))
            else:
                raise NotImplementedError

        return figures