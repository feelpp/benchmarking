import  reframe                 as rfm
import  reframe.utility.sanity  as sn


@rfm.simple_test
class HeatToolboxTest (rfm.RunOnlyRegressionTest):

    descr = 'Launch testcases from the Heat Toolbox'
    valid_systems = ['*']
    valid_prog_environs = ['*']

    reference = {}

    executable = 'feelpp_toolbox_heat'

    case = parameter([  '/usr/share/feelpp/data/testcases/toolboxes/heat/cases/Building/ThermalBridgesENISO10211/case2.cfg',
                        #'/usr/share/feelpp/data/testcases/toolboxes/heat/cases/Building/ThermalBridgesENISO10211/case3.cfg',
                        '/usr/share/feelpp/data/testcases/toolboxes/heat/cases/Building/ThermalBridgesENISO10211/case4.cfg' ])

    numTask = parameter([2,4,6])


    @run_before('run')
    def set_task_number(self):
        self.num_tasks = self.numTask
        self.num_tasks_per_node = 128
        self.num_cpus_per_task = 1

    @run_before('run')
    def set_launcher_options(self):
        self.job.launcher.options = ['-bind-to core', '--use-hwthread-cpus']


    @run_before('run')
    def set_executable_opts(self):
        self.executable_opts = [f'--config-file {self.case}']


    @performance_function('s', perf_key='Execution time')
    def extract_execution_time(self):
        return sn.extractsingle(r'execution time\s+(\S+)s', self.stdout, 1, float)


    @sanity_function
    def check_finished(self):
        return sn.assert_found('[ Stopping Feel++ ]', self.stdout)
