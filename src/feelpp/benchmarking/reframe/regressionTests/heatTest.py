import  reframe                 as rfm
import  reframe.utility.sanity  as sn


# Case 2 : 2d, temperature distribution and heat flow within a roof construction
# Case 3 : 3d, temperature distribution and heat flows through the wall-balcony junction
# Case 4 : 3d, temperature distribution and heat flows within a three dimensional thermal bridge consisting of an iron bar penetrating an insulation layer


@rfm.simple_test
class HeatToolboxTest (rfm.RunOnlyRegressionTest):

    # Test parametrisation
    case2 ='/usr/share/feelpp/data/testcases/toolboxes/heat/cases/Building/ThermalBridgesENISO10211/case2.cfg'
    case3 = '/usr/share/feelpp/data/testcases/toolboxes/heat/cases/Building/ThermalBridgesENISO10211/case3.cfg'
    case4 ='/usr/share/feelpp/data/testcases/toolboxes/heat/cases/Building/ThermalBridgesENISO10211/case4.cfg'

    case = parameter([case2, case4])#case3, case4])
    numTask = parameter([2,4,6])


    # Initialisation
    descr = 'Launch testcases from the Heat Toolbox'
    valid_systems = ['gaya', 'local']
    valid_prog_environs = ['env_gaya', 'env_local']

    reference = {
        'localCFG': {
            'Execution_time': (0, None, None, 's')
        }
    }

    executable = 'feelpp_toolbox_heat'


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
        self.executable_opts = [f'--config-file {self.case}', '--heat.scalability-save=1']


    @performance_function('s', perf_key='executionTime')
    def extract_execution_time(self):
        return sn.extractsingle(r'execution time\s+(\S+)s', self.stdout, 1, float)

    #@performance_function('s', perf_key='updateForUse')
    #def extract_updateTime(self):
    #    with open('\home\tanguy\feelppdb\toolboxes\heat\ThermalBridgesENISO10211\Case2\np_4', 'r') as file:
    #        sn.assert_found()



    @run_before('performance')
    def set_perf_variables(self):
        self.perf_variables = {
            'executionTime': self.extract_execution_time()
        }

    @sanity_function
    def check_finished(self):
        return sn.assert_found('[ Stopping Feel++ ]', self.stdout)
