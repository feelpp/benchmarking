
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

print(pd.__version__)

# Adapted from report.py for new test launching

# Replace 'your_file.json' with the path to your JSON file
# file_path = 'docs/modules/meluxina/pages/20231209/kub_scenario0.json'


class Report2:
    """
    Class to load the reframe report file, a json file, and extract the data

    :param file_path: path to the json file
    :type file_path: str

    """

    def __init__(self, file_path, ref_speedup=128):
        self.file_path = file_path
        self.data = None
        self.load()

        df = pd.DataFrame(self.data['runs'][0]['testcases'][0:])
        df['num_tasks'] = df['check_vars'].apply(lambda x: x['num_tasks'])
        df['num_tasks'] = df['num_tasks'].astype(int)
        self.df_perf = pd.DataFrame()
        for k, t in enumerate(df['num_tasks'].unique()):
            for i in df['perfvars'][k]:
                self.df_perf = pd.concat([self.df_perf, pd.DataFrame(
                    [{'num_tasks': t, 'name': i['name'], 'value': i['value']}])], ignore_index=True)

        self.df_perf['name'] = self.df_perf['name'].astype(str)
        self.df_perf['value'] = self.df_perf['value'].astype(float)
        self.df_perf['num_tasks'] = self.df_perf['num_tasks'].astype(int)

        # build a dataframe for the speedup with respect to 'ref_speedup' tasks
        self.df_speedup = pd.DataFrame()
        ref = self.df_perf[self.df_perf['num_tasks'] == ref_speedup]
        print(ref.to_markdown())

        for k, t in enumerate(df['num_tasks'].unique()):
            for i in df['perfvars'][k]:

                print()
                print(ref['value'].values[0]/i['value'])
                print(i['value'])

                self.df_speedup = pd.concat([self.df_speedup, pd.DataFrame(
                    [{'num_tasks': t, 'name': i['name'], 'value': ref['value'].values[0]/i['value']}])], ignore_index=True)
        # the optimal speedup is ref_speedup
        self.df_speedup['optimal'] = self.df_speedup['num_tasks'].apply(
            lambda x: x/ref_speedup)
        self.df_speedup['half optimal'] = self.df_speedup['num_tasks'].apply(
            lambda x: x/(2*ref_speedup))

    def load(self):
        with open(self.file_path, 'r') as file:
            self.data = json.load(file)

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

    def plotSteps(self):
        fig = go.Figure()
        for i in self.df_perf['name'].unique():
            fig.add_trace(go.Scatter(x=self.df_perf[self.df_perf['name'] == i]['num_tasks'],
                          y=self.df_perf[self.df_perf['name'] == i]['value'], name=i, mode='lines+markers'))
        fig.update_layout(yaxis_type="log")
        return fig

    def plotPerformanceByStep(self):
        fig = go.Figure()
        for t in sorted(self.df_perf['num_tasks'].unique(), reverse=False):
            df_task = self.df_perf[self.df_perf['num_tasks'] == t]
            fig.add_trace(
                go.Bar(x=df_task['name'], y=df_task['value'], name=str(t)))

        fig.update_layout(barmode='group', xaxis_tickangle=-45,
                          title='Performance of tasks', yaxis_type='log')
        return fig

    def plotPerformanceByTask(self):
        fig = px.bar(self.df_perf, x="num_tasks", y="value",
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
        fig.layout.update(title='Speedup')
        return fig
