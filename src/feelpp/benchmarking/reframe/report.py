
import os
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

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


# Names in Feel++ output document
partialPerfNames = {'init': ['initMaterialProperties', 'initMesh', 'initFunctionSpaces', 'initPostProcess', 'graph', 'matrixVector', 'algebraicOthers'],
                    'solve': ['ksp-niter', 'algebraic-assembly', 'algebraic-solve'] }

def isPartialPerf(name):
    return any(name in names for names in partialPerfNames.values())



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

        # Following attributes will be set using methods
        self.data               = None
        self.ref_speedup        = -1
        self.df_perf            = pd.DataFrame()
        self.df_speedup         = pd.DataFrame()
        self.df_partialPerf     = pd.DataFrame() if self.partial else None
        self.df_partialSpeedup  = pd.DataFrame() if self.partial else None

        self.load()
        self.processData()



    def load(self):
        with open(self.file_path, 'r') as file:
            self.data = json.load(file)


    def processData(self):
        # Needed dataframe for building df_perf and df_speedup
        df = pd.DataFrame(self.data['runs'][0]['testcases'][0:])
        df['num_tasks'] = df['check_vars'].apply(lambda x: x['num_tasks'])
        df['num_tasks'] = df['num_tasks'].astype(int)
        df = df[['num_tasks', 'perfvars']]

        self.buildPerf(df)
        self.buildSpeedup(df)



    def buildPerf(self, df):
        for k, t in enumerate(df['num_tasks'].unique()):
            for perf in df['perfvars'][k]:
                    if isPartialPerf(perf['name']):
                        self.df_partialPerf = pd.concat([self.df_partialPerf, pd.DataFrame(
                            [{'num_tasks': t, 'name': perf['name'], 'value': perf['value']}])], ignore_index=True)
                    else:
                        self.df_perf = pd.concat([self.df_perf, pd.DataFrame(
                            [{'num_tasks': t, 'name': perf['name'], 'value': perf['value']}])], ignore_index=True)

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
        print("Main performance variables:\n", mainRefs.to_markdown())

        if self.partial:
            partRefs = self.df_partialPerf[self.df_partialPerf['num_tasks'] == self.ref_speedup]
            print("Partial performances variables\n", partRefs.to_markdown())

        for k, t in enumerate(df['num_tasks'].unique()):
            mainIndex = 0
            partIndex = 0
            for perf in df['perfvars'][k]:

                if isPartialPerf(perf['name']):
                    self.df_partialSpeedup = pd.concat([self.df_partialSpeedup, pd.DataFrame(
                        [{'num_tasks': t, 'name': perf['name'], 'value': partRefs['value'].values[partIndex]/perf['value']}] )], ignore_index=True)
                    partIndex += 1
                else:
                    self.df_speedup = pd.concat([self.df_speedup, pd.DataFrame(
                        [{'num_tasks': t, 'name': perf['name'], 'value': mainRefs['value'].values[mainIndex]/perf['value']}] )], ignore_index=True)
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
        for i in self.df_perf['name'].unique():
            fig.add_trace(go.Scatter(x=self.df_perf[self.df_perf['name'] == i]['num_tasks'],
                          y=self.df_perf[self.df_perf['name'] == i]['value'], name=i, mode='lines+markers'))
        fig.update_layout(title='Steps', yaxis_type="log")
        return fig


    def plotPerformanceByStep(self):
        fig = go.Figure()
        for t in sorted(self.df_perf['num_tasks'].unique(), reverse=False):
            df_task = self.df_perf[self.df_perf['num_tasks'] == t]
            fig.add_trace(
                go.Bar(x=df_task['name'], y=df_task['value'], name=str(t)))

        fig.update_layout(barmode='group', xaxis_tickangle=-45,
                          title='Performance by step', yaxis_type='log')
        return fig


    def plotPerformanceByTask(self):
        fig = px.bar(self.df_perf, x="num_tasks", y="value", title='Performance by task',
                     color="name", barmode="group", log_y=True, log_x=True)
        return fig


    def plotSpeedup(self):
        fig = go.Figure()
        for t in self.df_speedup['name'].unique():
            df_task = self.df_speedup[self.df_speedup['name'] == t]
            fig.add_trace(go.Scatter(x=df_task['num_tasks'], y=df_task['value'],
                          mode='lines+markers', name=f'{df_task["name"].values[0]}'))

        fig.add_trace(go.Scatter(
            x=self.df_speedup['num_tasks'], y=self.df_speedup['optimal'], mode='lines', name='optimal'))
        fig.add_trace(go.Scatter(
            x=self.df_speedup['num_tasks'], y=self.df_speedup['half optimal'], mode='lines', name='half optimal'))
        fig.add_trace(go.Scatter(
            x=self.df_speedup['num_tasks'], y=self.df_speedup['optimal'], fill='tonexty', mode='none', name='optimal'))

        fig.layout.update(title='Speedup for main stages')
        return fig


    def plotPartialSpeedup(self, key):

        fig = go.Figure()
        partialNames = partialPerfNames[key]
        if key=='solve':
            partialNames.remove('ksp-niter')

        for t in partialNames:
            df_task = self.df_partialSpeedup[self.df_partialSpeedup['name'] == t]
            fig.add_trace(go.Scatter(x=df_task['num_tasks'], y=df_task['value'],
                                     mode='lines+markers', name=f'{df_task["name"].values[0]}'))

        fig.add_trace(go.Scatter(
            x=self.df_partialSpeedup['num_tasks'], y=self.df_partialSpeedup['optimal'], mode='lines', name='optimal'))
        fig.add_trace(go.Scatter(
            x=self.df_partialSpeedup['num_tasks'], y=self.df_partialSpeedup['half optimal'], mode='lines', name='half optimal'))
        fig.add_trace(go.Scatter(
            x=self.df_partialSpeedup['num_tasks'], y=self.df_partialSpeedup['optimal'], fill='tonexty', mode='none', name='optimal'))

        fig.layout.update(title=f'Speed up for {key} phase')
        return fig



if __name__ == "__main__":

    #case_path = "/home/tanguy/Projet/benchmarking/docs/modules/gaya/pages/reports/heat/Building/ThermalBridgesENISO10211/20240702-case3.json"
    case_path =  "/home/tanguy/Projet/benchmarking/build/TEST/RESULTS/ASYNC/20240719-case3-ASYNC.json"
    result = Report(file_path=case_path)

    figStep = result.plotSteps()
    figStep.show()

    figPerfStep = result.plotPerformanceByStep()
    figPerfStep.show()

    figPerfTask = result.plotPerformanceByTask()
    figPerfTask.show()

    figSpeedup = result.plotSpeedup()
    figSpeedup.show()

    figInitSpeedup = result.plotPartialSpeedup(key='init')
    figInitSpeedup.show()

    figSolveSpeedup = result.plotPartialSpeedup(key='solve')
    figSolveSpeedup.show()