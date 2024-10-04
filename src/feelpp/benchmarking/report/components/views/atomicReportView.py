import plotly.graph_objects as go
import plotly.express as px
from numpy import float64 as float64
from pandas import MultiIndex

class AtomicReportView:
    """ View component for the Atomic Report, it contains all figure generation related code """
    def plotScatters(self,df, title, yaxis_label):
        """ Create a plot with multiple lines
        Args:
            df (pd.DataFrame): Dataframe to create plot from, index goes to x axis and columns are line plots.
                                Values go on y-axis. The x-axis label is inferred from the dataframe's index name.
            title (str) : Title of the figure
            yaxis_label (str): Label of the y-axis
        Returns:
            go.Figure : Figure with multiple scatter plots
        """

        if isinstance(df.index,MultiIndex):
            if len(df.index.names)>2:
                print("WARNING: Too many dimensions, only two dimensions will be plotted.")

            colors = px.colors.qualitative.Alphabet

            fig = go.Figure()
            for i,col in enumerate(df.columns):
                for j,dim in enumerate(df.index.get_level_values(1).unique().values):
                    dim_name = df.index.names[1]
                    partial_df = df.xs(dim,level=dim_name,axis=0)
                    fig.add_trace(
                        go.Scatter(
                            x = partial_df.index,
                            y = partial_df.loc[:,col],
                            name=f"{col}",
                            line=dict(color=colors[i]),
                            showlegend=j==0,
                            text=f"{dim_name} = {dim}",
                            legendgroup=col,
                        )
                    )
            return fig
        else:
            return go.Figure(
                data = [
                    go.Scatter(
                        x = df.index,
                        y = df.loc[:,column],
                        name = column,
                    )
                    for column in df.columns
                ],
                layout=go.Layout(
                    title=title,
                    xaxis=dict( title = df.index.name ),
                    yaxis=dict( title = yaxis_label )
                )
            )

    def plotTable(self,df, precision = 3):
        """ Create a plotly table with the same structure as the input dataframe
        Args:
            df (pd.DataFrame): Dataframe to create the table from.
        Returns:
            go.Figure: A plotly figure with a go.Table trace
        """
        return go.Figure(
            go.Table(
                header=dict(values= [df.index.name] + df.columns.tolist()),
                cells=dict(
                    values=[df.index.values.tolist()] + [df[col] for col in df.columns],
                    format=[f'.{precision}f' if t == float64 else '' for t in [df.index.dtype] + df.dtypes.values.tolist()]
                )
            )
        )

    def plotSpeedup(self,df, title):
        """Create a plotly plot with multiple scatters representing the speedup of each stage
            It includes the Optimal and half optimal speedup, as well as a linear regression for all curves
        Args:
            df: (pd.DataFrame): Dataframe to create the figure from.
        Returns:
            go.Figure: A plotly figure with multiple go.Scatter traces
        """
        curve_names = [col for col in df.columns if col not in ["Optimal","HalfOptimal"] and not col.endswith("linearReg")]
        curves = []
        colors = px.colors.qualitative.Alphabet

        for i,col in enumerate(curve_names):
            color = colors[i]
            curves.append(
                go.Scatter(
                    x = df.index,
                    y = df.loc[:,col],
                    name = col,
                    legendgroup=col,
                    mode="lines+markers",
                    line=dict(color=color)
                )
            )
            curves.append(
                go.Scatter(
                    x = df.index,
                    y = df.loc[:,col+"_linearReg"],
                    name = col + "Linear Regression",
                    showlegend=False,
                    legendgroup=col,
                    mode="lines",
                    line=dict(dash="dash",color=color)
                )
            )

        return go.Figure(
            data = curves + [
                go.Scatter(
                    x = df.index,
                    y = df.loc[:,"HalfOptimal"],
                    mode = 'lines',
                    name = "HalfOptimal",
                    line=dict(color='grey', width=1)
                )
            ] + [
                go.Scatter(
                    x = df.index,
                    y = df.loc[:,"Optimal"],
                    mode = 'lines',
                    name = "Optimal",
                    line=dict(color='grey', width=1),
                    fill='tonexty',
                    fillcolor='rgba(0, 100, 255, 0.20)'
                )
            ],
            layout=go.Layout(
                title=title,
                xaxis=dict( title = df.index.name ),
            )
        )

    def plotSpeedupTable(self,df, precision = 3):
        """Create a plotly table for performance
        Args:
            df: (pd.DataFrame): Dataframe to create the table from.
        Returns:
            go.Figure: A plotly figure with a go.Table trace
        """
        return self.plotTable(
            df.loc[:,[col for col in df.columns if not col.endswith("linearReg")]],
            precision=precision
        )
