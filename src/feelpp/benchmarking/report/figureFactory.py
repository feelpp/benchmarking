import plotly.graph_objects as go
import plotly.express as px
from pandas import MultiIndex
from numpy import float64 as float64

from feelpp.benchmarking.report.transformationStrategies import TransformationStrategyFactory


class Figure:
    """ Abstract class for a figure """
    def __init__(self,plot_config,transformation_strategy):
        self.config = plot_config
        self.transformation_strategy = transformation_strategy

    def createMultiindexFigure(self,df):
        raise NotImplementedError("Pure virtual function. Not to be called from the base class")

    def createSimpleFigure(self,df):
        raise NotImplementedError("Pure virtual function. Not to be called from the base class")

    def createTraces(self,df):
        raise NotImplementedError("Pure virtual function. Not to be called from the base class")

    def updateLayout(self,fig):
        """ Updates the layout of a figure with general (shared) information.
        Args:
            - fig (go.Figure): The plotly figure to update the layout for
        Returns: (go.Figure) The updated plotly figure
        """
        fig.update_layout(
            title=self.config.title,
            xaxis=dict(title = self.config.xaxis.label),
            yaxis=dict(title = self.config.yaxis.label),
            legend=dict(title=self.config.color_axis.label if self.config.color_axis else "")
        )
        return fig

    def getIdealRange(self,df):
        """ Computes the [(min - eps), (max+eps)] interval for optimal y-axis display
        Args:
            - df (pd.DataFrame): The dataframe for which the interval should be computed
        Returns list[float, float]: The  [(min - eps), (max+eps)] interval
        """
        range_epsilon= 0.01
        return [ df.min().min() - df.min().min()*range_epsilon, df.max().max() + df.min().min()*range_epsilon ]

    def createSliderAnimation(self,df):
        """ Creates a plotly slider animation figure from a pandas dataframe. Depending on the provided config parameters.
        The slider axis corresponds to the secondary_axis parameter of the configuration file.
        Args:
            - df (pd.DataFrame): The dataframe containing the figure data.
        Returns: (go.Figure) The plotly slider animation figure
        """
        frames = []
        ranges=[]
        anim_dimension_values = df.index.get_level_values(self.config.secondary_axis.parameter).unique().values

        for dim in anim_dimension_values:
            frame_df = df.xs(dim,level=self.config.secondary_axis.parameter,axis=0)
            frames.append(self.createTraces(frame_df))
            ranges.append(self.getIdealRange(frame_df))

        if frames:
            fig = go.Figure(
                data = frames[0],
                frames = [
                    go.Frame( data = f, name=f"frame_{i}", layout=dict( yaxis=dict(range = ranges[i]) ) )
                    for i,f in enumerate(frames)
                ],
                layout=go.Layout(
                    sliders=[dict(
                        active=0, currentvalue=dict(prefix=f"{self.config.secondary_axis.label} = "), transition = dict(duration= 0),
                        steps=[dict(label=f"{h}",method="animate",args=[[f"frame_{k}"],dict(mode="immediate",frame=dict(duration=0, redraw=True))]) for k,h in enumerate(anim_dimension_values)],
                    )],
                    yaxis=dict(range = ranges[0]),
                )
            )
        else:
            fig = go.Figure()
        return fig

    def createFigure(self,df):
        """ Creates a figure from the master dataframe
        Args:
            df (pd.DataFrame). The master dataframe containing all reframe test data
        Returns:
            go.Figure: Plotly figure corresponding to the grouped Bar type
        """
        df = self.transformation_strategy.calculate(df)

        if isinstance(df.index,MultiIndex):
            figure = self.createMultiindexFigure(df)
        else:
            figure = self.createSimpleFigure(df)

        figure.update_layout(self.config.layout_modifiers)
        figure = self.updateLayout(figure)
        return figure


class ScatterFigure(Figure):
    """ Concrete Figure class for scatter figures """
    def __init__(self, plot_config,transformation_strategy,fill_lines=[]):
        super().__init__(plot_config,transformation_strategy)
        self.fill_lines = fill_lines

    def createTraces(self,df):
        """ Creates the traces for a given dataframe. Useful for animation creation.
        Args:
            - df (pd.DataFrame): The dataframe containing the figure data.
        Returns: (list[go.Trace]) The Scatter traces to display in the scatter figure.
        """
        return [
            go.Scatter( x = df.index, y = df.loc[:,col], name = col, fill='tonexty' if i > 0 else None, line=dict(color="black",dash="dash") ,mode="lines")
            for i,col in enumerate(self.fill_lines)
        ] + [
            go.Scatter( x = df.index, y = df.loc[:,col], name = col )
            for col in [c for c in df.columns if c not in self.fill_lines]
        ]

    def createMultiindexFigure(self,df):
        """ Creates a plotly figure from a multiIndex dataframe
        Args:
            df (pd.DataFrame). The transformed dataframe (must be multiindex)
        Returns:
            go.Figure: Scatter animation where the secondary_ axis corresponds to a specified parameter
        """
        return self.createSliderAnimation(df)

    def createSimpleFigure(self,df):
        """ Creates a plotly figure from a given dataframe
        Args:
            df (pd.DataFrame). The transformed dataframe
        Returns:
            go.Figure: Scatter plot
        """
        return go.Figure(data = self.createTraces(df))


class TableFigure(Figure):
    """ Concrete Figure class for scatter figures """
    def __init__(self, plot_config, transformation_strategy):
        super().__init__(plot_config, transformation_strategy)
        self.precision = 3

    def cellFormat(self,df):
        """ Computes the expected format of a table cell, expected by Plotly, depending on the precision and the dataframe dtypes.
        Args:
            df (pd.DataFrame) DataFrame containing table data.
        Returns
            list[float|'']. List containing the Table expected cell formats
        """
        return [f'.{self.precision}' if t == float64 else '' for t in [df.index.dtype] + df.dtypes.values.tolist()]

    def createMultiindexFigure(self,df):
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
                    format=self.cellFormat(df)
                )
            )
        )

    def createSimpleFigure(self,df):
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
                    format=self.cellFormat(df)
                )
            )
        )

    def updateLayout(self, fig):
        """ Do not update general layout defined by the parent method """
        pass
        return fig



class StackedBarFigure(Figure):
    """ Concrete Figure class for stacked bar charts"""
    def __init__(self, plot_config, transformation_strategy):
        super().__init__(plot_config, transformation_strategy)

    def createMultiindexFigure(self,df):
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
        return fig

    def createSimpleFigure(self,df):
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
            layout=go.Layout( barmode="stack",xaxis=dict(title = self.config.xaxis.label))
        )

    def updateLayout(self,fig):
        """ Sets the title, yaxis and legend attributes of the layout without specifying the xaxis"""
        fig.update_layout(
            title=self.config.title,
            yaxis=dict(title = self.config.yaxis.label),
            legend=dict(title=self.config.color_axis.label if self.config.color_axis else "")
        )
        return fig

class GroupedBarFigure(Figure):
    def __init__(self, plot_config, transformation_strategy):
        super().__init__(plot_config, transformation_strategy)

    def createTraces(self,df):
        """ Creates the Bar traces for a given dataframe. Useful for animation creation.
        Args:
            - df (pd.DataFrame): The dataframe containing the figure data.
        Returns: (list[go.Trace]) The Bar traces to display in the scatter figure.
        """
        return [
            go.Bar(x = df.index.astype(str), y = df.loc[:,col],name=col)
            for col in df.columns
        ]

    def createMultiindexFigure(self,df):
        """ Creates a plotly figure from a multiIndex dataframe
        Args:
            df (pd.DataFrame). The transformed dataframe (must be multiindex)
        Returns:
            go.Figure: Bar animation where the secondary_ axis corresponds to a specified parameter
        """
        return self.createSliderAnimation(df)

    def createSimpleFigure(self,df):
        """ Creates a plotly figure from a given dataframe
        Args:
            df (pd.DataFrame). The transformed dataframe
        Returns:
            go.Figure: Bar plot
        """
        return go.Figure(self.createTraces(df))


class FigureFactory:
    """ Factory class to dispatch concrete figure elements"""
    @staticmethod
    def create(plot_config):
        """ Creates a concrete figure element
        Args:
            plot_config (Plot). Pydantic object with the plot configuration information
        """
        strategy = TransformationStrategyFactory.create(plot_config)
        figures = []
        for plot_type in plot_config.plot_types:
            if plot_type ==  "scatter":
                fill_lines = []
                if plot_config.transformation=="speedup":
                    fill_lines = ["optimal","half-optimal"]
                figures.append(ScatterFigure(plot_config,strategy, fill_lines))
            elif plot_type == "table":
                figures.append(TableFigure(plot_config,strategy))
            elif plot_type == "stacked_bar":
                figures.append(StackedBarFigure(plot_config,strategy))
            elif plot_type == "grouped_bar":
                figures.append(GroupedBarFigure(plot_config,strategy))
            else:
                raise NotImplementedError

        return figures