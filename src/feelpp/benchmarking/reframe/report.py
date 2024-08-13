
import os
import json
import pandas               as pd
import plotly.graph_objects as go
import plotly.express       as px
import plotly.colors        as pc

from plotly.subplots        import make_subplots
from sklearn.linear_model   import LinearRegression

print(pd.__version__)

# Replace 'your_file.json' with the path to your JSON file
# file_path = 'docs/modules/meluxina/pages/20231209/kub_scenario0.json'


# Tests with only main references
notPartial = [  '20231201-1430.json',
                '20231207-1600.json',
                '20231209-0040.json',
                '20231211-0600.json',
                '20231211-1248.json',
                'kub_scenario0.json'    ]



class Report:
    """
    Class to load the reframe report file, a json file, and extract the data

    :param file_path: path to the json file
    :type file_path: str

    """

    def __init__(self, file_path):

        self.file_path = file_path
        self.partial = False
        if os.path.basename(self.file_path) not in notPartial:
            self.partial = True

        # Following attributes will be set while processing the data
        self.data               = None
        self.toolbox            = ''
        self.ref_speedup        = -1
        self.df_perf            = pd.DataFrame()
        self.df_speedup         = pd.DataFrame()
        self.df_partialPerf     = pd.DataFrame() if self.partial else None
        self.df_partialSpeedup  = pd.DataFrame() if self.partial else None
        self.partialDict        = dict() if self.partial else None

        self.load()
        self.processData()


    def load(self):
        with open(self.file_path, 'r') as file:
            self.data = json.load(file)


    def processData(self):
        # Avoids error for reporting scale performances not launched with 'CpuVariation.py'
        try:
            self.toolbox = self.data['runs'][0]['testcases'][0]['check_vars']['toolbox']
        except KeyError as e:
            self.toolbox = ''

        # Needed dataframe for building df_perf and df_speedup
        df = pd.DataFrame(self.data['runs'][0]['testcases'][0:])
        df['num_tasks'] = df['check_vars'].apply(lambda x: x['num_tasks'])
        df['num_tasks'] = df['num_tasks'].astype(int)
        df = df[['num_tasks', 'perfvars']]

        if self.partial:
            self.buildPartialDict()
        self.buildPerf(df)
        self.buildSpeedup(df)
        self.linearReg(self.df_speedup)
        if self.partial:
            self.linearReg(self.df_partialSpeedup)


    def buildPartialDict(self):
        constructorNames = []
        solveNames = []
        postprocessingNames = []

        # The building for heatfluid could have been done in a separate function,
        # but in this way we load the data only once
        if self.toolbox == 'heatfluid':
            heatConstructorNames = []
            heatPostprocessingNames = []
            fluidConstructorNames = []
            fluidPostprocessingNames = []

        for perfvar in self.data['runs'][0]['testcases'][0]['perfvars']:
            name = perfvar['name']

            if self.toolbox == 'heatfluid':
                if name.startswith('CONSTRUCTOR_H_'):
                    heatConstructorNames.append(name.replace('CONSTRUCTOR_', ''))
                    continue
                elif name.startswith('POSTPROCESSING_H_'):
                    heatPostprocessingNames.append(name.replace('POSTPROCESSING_', ''))
                    continue
                elif name.startswith('CONSTRUCTOR_F_'):
                    fluidConstructorNames.append(name.replace('CONSTRUCTOR_', ''))
                    continue
                elif name.startswith('POSTPROCESSING_F_'):
                    fluidPostprocessingNames.append(name.replace('POSTPROCESSING_', ''))
                    continue

            if name.startswith('CONSTRUCTOR_'):
                constructorNames.append(name.replace('CONSTRUCTOR_', ''))
            elif name.startswith('SOLVE_'):
                solveNames.append(name.replace('SOLVE_', ''))
            elif name.startswith('POSTPROCESSING_'):
                postprocessingNames.append(name.replace('POSTPROCESSING_', ''))

        constructorPart = constructorNames.pop()
        solvePart = solveNames.pop()
        postprocPart = postprocessingNames.pop()

        self.partialDict[constructorPart] = constructorNames
        self.partialDict[solvePart] = solveNames
        self.partialDict[postprocPart] = postprocessingNames

        if self.toolbox == 'heatfluid':
            heatConstructorPart = heatConstructorNames.pop()
            heatPostprocessingPart = heatPostprocessingNames.pop()
            fluidConstructorPart = fluidConstructorNames.pop()
            fluidPostprocessingPart = fluidPostprocessingNames.pop()

            self.partialDict[heatConstructorPart] = heatConstructorNames
            self.partialDict[heatPostprocessingPart] = heatPostprocessingNames
            self.partialDict[fluidConstructorPart] = fluidConstructorNames
            self.partialDict[fluidPostprocessingPart] = fluidPostprocessingNames


    def isPartialPerf(self, name):
        if self.partial:
            return any(name in names for names in self.partialDict.values())
        else:
            return False


    def buildPerf(self, df):
        for k, t in enumerate(df['num_tasks'].unique()):
            for perf in df['perfvars'][k]:
                name = perf['name']
                nameWithoutPrefix = name.split('_',1)[-1]
                if self.isPartialPerf(nameWithoutPrefix):
                    self.df_partialPerf = pd.concat([self.df_partialPerf, pd.DataFrame(
                        [{'num_tasks': t, 'name': nameWithoutPrefix, 'value': perf['value']}])], ignore_index=True)
                else:
                    self.df_perf = pd.concat([self.df_perf, pd.DataFrame(
                        [{'num_tasks': t, 'name': nameWithoutPrefix, 'value': perf['value']}])], ignore_index=True)

        self.df_perf['name'] = self.df_perf['name'].astype(str)
        self.df_perf['value'] = self.df_perf['value'].astype(float)
        self.df_perf['num_tasks'] = self.df_perf['num_tasks'].astype(int)

        if self.partial:
            self.df_partialPerf['name'] = self.df_partialPerf['name'].astype(str)
            self.df_partialPerf['value'] = self.df_partialPerf['value'].astype(float)
            self.df_partialPerf['num_tasks'] = self.df_partialPerf['num_tasks'].astype(int)


    def buildSpeedup(self, df):
        self.ref_speedup = df['num_tasks'].min()

        mainRefs = self.df_perf[self.df_perf['num_tasks'] == self.ref_speedup]
        if self.partial:
            partRefs = self.df_partialPerf[self.df_partialPerf['num_tasks'] == self.ref_speedup]

        for k, t in enumerate(df['num_tasks'].unique()):
            mainIndex = 0
            partIndex = 0
            for perf in df['perfvars'][k]:
                name = perf['name']
                nameWithoutPrefix = name.split('_',1)[-1]

                if self.isPartialPerf(nameWithoutPrefix):
                    self.df_partialSpeedup = pd.concat([self.df_partialSpeedup, pd.DataFrame(
                        [{'num_tasks': t, 'name': nameWithoutPrefix, 'value': partRefs['value'].values[partIndex]/perf['value']}] )], ignore_index=True)
                    partIndex += 1
                else:
                    self.df_speedup = pd.concat([self.df_speedup, pd.DataFrame(
                        [{'num_tasks': t, 'name': nameWithoutPrefix, 'value': mainRefs['value'].values[mainIndex]/perf['value']}] )], ignore_index=True)
                    mainIndex += 1

        # The optimal speedup is ref_speedup
        lambda1 = lambda x: x/self.ref_speedup
        lambda2 = lambda x: x/(2*self.ref_speedup)

        self.df_speedup['optimal'] = self.df_speedup['num_tasks'].apply(lambda1)
        self.df_speedup['half optimal'] = self.df_speedup['num_tasks'].apply(lambda2)

        if self.partial:
            self.df_partialSpeedup = self.df_partialSpeedup[self.df_partialSpeedup['name'] !='ksp-niter']
            self.df_partialSpeedup['optimal'] = self.df_partialSpeedup['num_tasks'].apply(lambda1)
            self.df_partialSpeedup['half optimal'] = self.df_partialSpeedup['num_tasks'].apply(lambda2)


    def linearReg(self, df):
        """
        Extends df with linear regression values
        """
        for perf in df['name'].unique():
            df2 = df[df['name'] == perf]
            x = df2['num_tasks'].values.reshape(-1,1)
            y = df2['value'].values
            model = LinearRegression()
            model.fit(x,y)
            y_pred = model.predict(x)
            slope = model.coef_[0]
            origin = model.intercept_

            df.loc[df['name']==perf, 'linearRegression'] = y_pred
            df.loc[df['name']==perf, 'slope'] = slope
            df.loc[df['name']==perf, 'origin'] = origin


    def extractSessionInfo(self):
        """
        Extracts and returns session information from the JSON data.
        """
        if 'session_info' in self.data:
            session = self.data['session_info']
            return {
                'cmdline': session.get('cmdline', 'N/A'),
                'config_files': session.get('config_files', []),
                'data_version': session.get('data_version', 'N/A'),
                'hostname': session.get('hostname', 'N/A'),
                'log_files': session.get('log_files', []),
                'prefix_output': session.get('prefix_output', 'N/A'),
                'prefix_stage': session.get('prefix_stage', 'N/A'),
                'user': session.get('user', 'N/A'),
                'version': session.get('version', 'N/A'),
                'workdir': session.get('workdir', 'N/A'),
                'time_start': session.get('time_start', 'N/A'),
                'time_end': session.get('time_end', 'N/A'),
                'time_elapsed': session.get('time_elapsed', 0),
                'num_cases': session.get('num_cases', 0),
                'num_failures': session.get('num_failures', 0)
            }
        else:
            return {}


    def printSessionInfo(self):
        for key, value in self.extractSessionInfo().items():
            print(f"{key}: {value}")

    def data(self):
        return self.data

    def testcases(self):
        return self.data['runs'][0]['testcases']

    def perfvars(self):
        return self.data['runs'][0]['testcases'][0]['perfvars']

    def check_vars(self):
        return self.data['runs'][0]['testcases'][0]['check_vars']

    def perf(self):
        return self.df_perf

    def speedup(self):
        return self.df_speedup

    def ref_speedup(self):
        return self.ref_speedup

    def partialPerfs(self):
        return self.df_partialPerf

    def partialSpeedUp(self):
        return self.df_partialSpeedup


    def plotSteps(self):
        fig = go.Figure()
        for name in self.df_perf['name'].unique():
            fig.add_trace(go.Scatter(x=self.df_perf[self.df_perf['name'] == name]['num_tasks'],
                          y=self.df_perf[self.df_perf['name'] == name]['value'], name=name, mode='lines+markers'))

        fig.update_layout(title='Steps', yaxis_type="log")
        return fig


    def plotTable(self, df, precision=3):
        table = go.Table(   header=dict(values=list(df.columns)),
                            cells=dict(values=[df[col] for col in df.columns], format=['', '', f'.{precision}f']))
        # First 2 columns are always int, str (num_tasks, perfname), don't need any format
        return table


    def plotPerformanceByStep(self):
        fig = make_subplots(rows=2, cols=1, vertical_spacing=0.5, specs = [[{"type": "scatter"}], [{"type": "table"}]])

        for t in sorted(self.df_perf['num_tasks'].unique(), reverse=False):
            df_task = self.df_perf[self.df_perf['num_tasks'] == t]
            fig.add_trace(go.Bar(x=df_task['name'], y=df_task['value'], name=str(t)), row=1, col=1)

        table = self.plotTable(self.df_perf)
        fig.add_trace(table, row=2, col=1)

        fig.update_layout(barmode='group', xaxis_tickangle=-45, title='Performance by step', yaxis_type='log')
        return fig


    def plotPerformanceByTask(self):
        fig = px.bar(self.df_perf, x="num_tasks", y="value", title='Performance by task',
                     color="name", barmode="group", log_y=True, log_x=True)
        return fig


    def buildButtons(self, nbCurves):
        """
        Builds 'toggle' buttons for displaying regression and optimality curves or not
        Index = n-th 'fig.add_trace()' call, starting by 0
        """
        regIndex = list(range(1, nbCurves-2, 2))
        optiIndex = list(range(nbCurves-3, nbCurves))
        menu = [dict(   type="buttons",
                        buttons=[dict(  label="Display linear regression",
                                        method="update",
                                        args=[{"visible":True}, {}, regIndex],
                                        args2=[{"visible":False}, {}, regIndex]
                                    ),
                                dict(   label="Display optimality",
                                        method="update",
                                        args=[{"visible":True}, {}, optiIndex],
                                        args2=[{"visible":False}, {}, optiIndex]
                                    )],
                        active=-1,
                        showactive=True,
                        x=0,
                        xanchor="left",
                        y=1.15,
                        yanchor="top",
                        direction="left"
                    )]
        return menu


    def plotSpeedup(self):
        fig = make_subplots(rows=2, cols=1, vertical_spacing=0.2, specs=[[{"type": "scatter"}], [{"type": "table"}]])
        colors = pc.qualitative.Plotly

        # Real traces
        for i,task in enumerate(self.df_speedup['name'].unique()):
            df_task = self.df_speedup[self.df_speedup['name'] == task]
            slope = df_task['slope'].unique()[0] * 100

            fig.add_trace(go.Scatter(x=df_task['num_tasks'], y=df_task['value'],
                                    mode='lines+markers', name=f'{df_task["name"].values[0]}', line=dict(color=colors[i])), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_task['num_tasks'], y=df_task['linearRegression'],
                                    mode='lines', name=f'{slope:.1f}%', line=dict(dash='dash', color=colors[i], width=1), visible=False), row=1, col=1)

        # Optimality traces
        fig.add_trace(go.Scatter(x=self.df_speedup['num_tasks'], y=self.df_speedup['optimal'], mode='lines', name='Optimal', line=dict(color='grey', width=1), visible=False))
        fig.add_trace(go.Scatter(x=self.df_speedup['num_tasks'], y=self.df_speedup['half optimal'], mode='lines', name='Semi-optimal', line=dict(color='grey', width=1), visible=False))
        fig.add_trace(go.Scatter(x=self.df_speedup['num_tasks'], y=self.df_speedup['optimal'], fill='tonexty', fillcolor='rgba(0, 100, 255, 0.20)', mode='none', name='Optimal area', visible=False))
        nbCurves = len(fig.data)

        # Table
        df = self.df_speedup[['num_tasks', 'name', 'value', 'linearRegression', 'slope']]
        table = self.plotTable(df)
        fig.add_trace(table, row=2, col=1)

        fig.update_layout(title='Speedup for main stages', updatemenus=self.buildButtons(nbCurves))
        return fig


    def plotPartialSpeedup(self, key):
        fig = make_subplots(rows=2, cols=1, vertical_spacing=0.2, specs = [[{"type": "scatter"}], [{"type": "table"}]])
        partialNames = self.partialDict[key]
        colors = pc.qualitative.Plotly

        # We don't want a curve from the number of iteration
        if 'solve' in key:
            for name in partialNames:
                if '-niter' in name:
                    partialNames.remove(name)
                    continue

        # Real traces
        for i,task in enumerate(partialNames):
            df_task = self.df_partialSpeedup[self.df_partialSpeedup['name'] == task]
            slope = df_task['slope'].unique()[0] * 100
            fig.add_trace(go.Scatter(x=df_task['num_tasks'], y=df_task['value'],
                                    mode='lines+markers', name=f'{df_task["name"].values[0]}', line=dict(color=colors[i])), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_task['num_tasks'], y=df_task['linearRegression'],
                                    mode='lines', name=f'{slope:.1f}%', line=dict(dash='dash', color=colors[i], width=1), visible=False), row=1, col=1)

        # Optimality traces
        fig.add_trace(go.Scatter(x=self.df_partialSpeedup['num_tasks'], y=self.df_partialSpeedup['optimal'], mode='lines', name='Optimal', line=dict(color='grey', width=1), visible=False))
        fig.add_trace(go.Scatter(x=self.df_partialSpeedup['num_tasks'], y=self.df_partialSpeedup['half optimal'], mode='lines', name='Semi-optimal', line=dict(color='grey', width=1), visible=False))
        fig.add_trace(go.Scatter(x=self.df_partialSpeedup['num_tasks'], y=self.df_partialSpeedup['optimal'], fill='tonexty', fillcolor='rgba(0, 100, 255, 0.20)', mode='none', name='Optimal area', visible=False))
        nbCurves = len(fig.data)

        # Table
        df = self.df_partialSpeedup[['num_tasks', 'name', 'value', 'linearRegression', 'slope']]
        table = self.plotTable(df)
        fig.add_trace(table, row=2, col=1)

        fig.layout.update(title=f'Speed up for {key} phase', updatemenus=self.buildButtons(nbCurves))
        return fig



# For debugging purposes:

if __name__ == "__main__":
    case_path = "/home/tanguy/Projet/benchmarking/docs/modules/gaya/pages/reports/heat/20240804-ThermalBridgesCase3.json"
    #case_path = "/home/tanguy/Projet/benchmarking/docs/modules/gaya/pages/reports/heatfluid/20240804-proneEye-M2-simple.json"
    #case_path = "/home/tanguy/Projet/benchmarking/docs/modules/meluxina/pages/kub/scenario0/20231211-1248.json"

    result = Report(file_path=case_path)

    figStep = result.plotSteps()
    figStep.show()

    figPerfStep = result.plotPerformanceByStep()
    figPerfStep.show()

    figPerfTask = result.plotPerformanceByTask()
    figPerfTask.show()

    figSpeedup = result.plotSpeedup()
    figSpeedup.show()

    if result.partial:
        for name, value in result.partialDict.items():
            if value != []:
                figPartialSpeedup = result.plotPartialSpeedup(key=name)
                figPartialSpeedup.show()