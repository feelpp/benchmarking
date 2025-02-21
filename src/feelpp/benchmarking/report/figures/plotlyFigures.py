import plotly.graph_objects as go
import plotly.express as px

from feelpp.benchmarking.report.figures.base import Figure
from numpy import float64 as float64
from pandas import factorize as pd_factorize


class PlotlyFigure(Figure):
    """ Base class for a Plotly figure """
    def __init__(self, plot_config, transformation_strategy):
        super().__init__(plot_config, transformation_strategy)

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

    def createSliderAnimation(self,df):
        """ Creates a plotly slider animation figure from a pandas dataframe. Depending on the provided config parameters.
        The slider axis corresponds to the secondary_axis parameter of the configuration file.
        Args:
            - df (pd.DataFrame): The dataframe containing the figure data.
        Returns: (go.Figure) The plotly slider animation figure
        """
        frames = []
        ranges=[]
        secondary_axis = self.transformation_strategy.dimensions["secondary_axis"]
        anim_dimension_values = df.index.get_level_values(secondary_axis).unique().values

        for dim in anim_dimension_values:
            frame_df = df.xs(dim,level=secondary_axis,axis=0)
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

    def createMultiindexFigure(self,df):
        """ Creates a plotly figure from a multiIndex dataframe
        Args:
            df (pd.DataFrame). The transformed dataframe (must be multiindex)
        Returns:
            go.Figure: animation where the secondary_ axis corresponds to a specified parameter
        """
        return self.createSliderAnimation(df)

    def createSimpleFigure(self,df):
        """ Creates a plotly figure from a given dataframe
        Args:
            df (pd.DataFrame). The transformed dataframe
        Returns:
            go.Figure: plot
        """
        return go.Figure(self.createTraces(df))

    def createFigure(self,df):
        """ Creates a figure from the master dataframe
        Args:
            df (pd.DataFrame). The master dataframe containing all reframe test data
        Returns:
            go.Figure: Plotly figure corresponding to the grouped Bar type
        """
        figure = super().createFigure(df)
        figure.update_layout(self.config.layout_modifiers)
        figure = self.updateLayout(figure)
        return figure

    def createHtml(self,df):
        return self.createFigure(df).to_html()


class PlotlyScatterFigure(PlotlyFigure):
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


class PlotlyTableFigure(PlotlyFigure):
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


class PlotlyStackedBarFigure(PlotlyFigure):
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
        xaxis = self.transformation_strategy.dimensions["xaxis"]
        secondary_axis = self.transformation_strategy.dimensions["secondary_axis"]

        fig = px.bar(
            df.reset_index().astype({
                secondary_axis:"str",
                xaxis:"str"
            }).rename(
                columns = {
                    xaxis:self.config.xaxis.label,
                    secondary_axis:self.config.secondary_axis.label
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


class PlotlyGroupedBarFigure(PlotlyFigure):
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

class PlotlyHeatmapFigure(PlotlyFigure):
    def __init__(self, plot_config, transformation_strategy):
        super().__init__(plot_config, transformation_strategy)

    def createTraces(self, df):
        """ Creates the Heatmap traces for a given dataframe. Useful for animation creation.
        Args:
            - df (pd.DataFrame): The dataframe containing the figure data.
        Returns: (go.Trace) The Heatmap traces to display in the scatter figure.
        """
        return go.Heatmap(
                x=df.index.astype(str),
                y=df.columns.astype(str),
                z=df.T.values,
                colorbar = dict(
                    title = self.config.yaxis.label
                )
            )

    def updateLayout(self, fig):
        """ Sets the title, yaxis and legend attributes of the layout"""
        fig.update_layout(
            title=self.config.title,
            xaxis=dict(title=self.config.xaxis.label),
            yaxis=dict(title=self.config.color_axis.label)
        )
        return fig


class PlotlySunburstFigure(PlotlyFigure):
    def __init__(self, plot_config, transformation_strategy):
        super().__init__(plot_config, transformation_strategy)

    def createMultiindexFigure(self, df):
        """ Creates the Sunburst traces for a given dataframe. Useful for animation creation.
        Args:
            - df (pd.DataFrame): The dataframe containing the figure data.
        Returns: (go.Trace) The Sunburst traces to display in the scatter figure.
        """
        return px.sunburst(
            df.reset_index(level=[0,1]).melt(value_vars=df.columns,id_vars=df.index.names),
            path=df.index.names+[df.columns.name],
            values = "value"
        )

    def createSimpleFigure(self, df):
        """ Creates a Plotly Sunburst figure from a given dataframe
        Args:
            df (pd.DataFrame). The transformed dataframe
        Returns:
            go.Figure: Plotly Sunburst figure
        """
        return px.sunburst(
            df.reset_index().melt(value_vars=df.columns,id_vars=df.index.name),
            path = [df.index.name,df.columns.name],
            values = "value",
        )

    def updateLayout(self, fig):
        """ Sets the title, yaxis and legend attributes of the layout"""
        fig.update_layout(
            title=self.config.title,
        )
        return fig

class PlotlyParallelcoordinatesFigure(PlotlyFigure):
    def __init__(self, plot_config, transformation_strategy):
        super().__init__(plot_config, transformation_strategy)

    @staticmethod
    def encodeFactorize(df):
        melted_factorized = df.copy()
        for column in df.columns:
            if df[column].dtype == "object":
                melted_factorized[column],_ = pd_factorize(df[column])
        return melted_factorized

    def createSimpleFigure(self, df):
        melted = df.reset_index().melt(value_vars=df.columns, id_vars=df.index.name)
        melted_factorized = self.encodeFactorize(melted)

        return go.Figure(
            go.Parcoords(
                line=dict(color=melted_factorized["value"], colorscale='Electric', showscale=True),
                dimensions = list(
                    [
                        dict( label = df.index.name, values = melted_factorized[df.index.name], tickvals = melted_factorized[df.index.name], ticktext = melted[df.index.name] ),
                        dict( label = df.columns.name, values = melted_factorized[df.columns.name], tickvals = melted_factorized[df.columns.name], ticktext = melted[df.columns.name] )
                    ]
                )
            )
        )

    def createMultiindexFigure(self, df):
        melted = df.reset_index().melt(value_vars=df.columns,id_vars=df.index.names)
        melted_factorized = self.encodeFactorize(melted)

        return go.Figure(
            go.Parcoords(
                line=dict(color=melted_factorized["value"], colorscale='Electric', showscale=True),
                dimensions = list(
                    [
                        dict( label = ind, values = melted_factorized[ind], tickvals = melted_factorized[ind], ticktext = melted[ind] )
                        for ind in df.index.names
                    ] + [
                        dict( label = df.columns.name, values = melted_factorized[df.columns.name], tickvals = melted_factorized[df.columns.name], ticktext = melted[df.columns.name] )
                    ]
                )
            )
        )


    def updateLayout(self, fig):
        """ Sets the title, yaxis and legend attributes of the layout"""
        fig.update_layout(title=self.config.title, legend=dict(title=self.config.yaxis.label))
        return fig


class Plotly3DFigure(PlotlyFigure):
    def __init__(self, plot_config, transformation_strategy):
        super().__init__(plot_config, transformation_strategy)
        if len(self.transformation_strategy.dimensions["extra_axes"])>0:
            self.y_axis = self.transformation_strategy.dimensions["extra_axes"][0]
            self.y_axis_label = self.config.extra_axes[0].label
        else:
            self.y_axis = self.transformation_strategy.dimensions["secondary_axis"]
            self.y_axis_label = self.config.secondary_axis.label if self.y_axis else self.config.color_axis.label if self.config.color_axis else ""

    def createMultiindexFigure(self, df):
        if len(df.index.names) == 2:
            return super().createSimpleFigure(df) #3D simple figure is equivalent to a multiindex 2D figure
        elif len(df.index.names) == 3:
            return super().createMultiindexFigure(df)
        else:
            raise ValueError("3D figures can only be created from 2 or 3 level multiindex dataframes")

    def createSimpleFigure(self, df):
        raise ValueError("Secondary axis must be specified for 3d Figures")

    def updateLayout(self, fig):
        """ Sets the title, yaxis and legend attributes of the layout"""
        fig.update_layout(
            title=self.config.title,
            legend=dict(title=self.config.color_axis.label if self.config.color_axis else "")
        )
        fig.update_scenes(
            xaxis_title=self.config.xaxis.label,
            yaxis_title=self.y_axis_label,
            zaxis_title=self.config.yaxis.label
        )
        return fig

class PlotlyScatter3DFigure(Plotly3DFigure):
    def __init__(self, plot_config, transformation_strategy):
        super().__init__(plot_config, transformation_strategy)

    def createTraces(self, df):
        """ Creates a 3D scatter plot traces
        Args:
            df (pd.DataFrame). The transformed dataframe (must be multiindex)
        Returns:
            go.Figure: 3D scatter plot
        """
        return [
            go.Scatter3d(
                x=df.index.get_level_values(self.transformation_strategy.dimensions["xaxis"]),
                y=df.index.get_level_values(self.y_axis),
                z=df[col],
                mode='markers', name=col
            )
            for col in df.columns
        ]


class PlotlySurface3DFigure(Plotly3DFigure):
    def __init__(self, plot_config, transformation_strategy):
        super().__init__(plot_config, transformation_strategy)

    def createTraces(self, df):
        """ Creates a 3D surface plot traces
        Args:
            df (pd.DataFrame). The transformed dataframe (must be multiindex)
        Returns:
            go.Figure: 3D surface plot
        """
        return [
            go.Mesh3d(
                x=df.index.get_level_values(self.transformation_strategy.dimensions["xaxis"]),
                y=df.index.get_level_values(self.y_axis),
                z=df[col],
                opacity=0.5, name=col
            )
            for col in df.columns
        ]


class PlotlyRadarFigure(PlotlyFigure):
    pass