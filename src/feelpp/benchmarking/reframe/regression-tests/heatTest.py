import  reframe                 as rfm
import  reframe.utility.sanity  as sn


@rfm.simple_test
class HeatToolboxTest (rfm.RunOnlyRegressionTest):

    # Initialisation
    descr = 'Launch testcases from the Heat Toolbox'
    valid_systems = ['gaya']
    valid_prog_environs = ['env_gaya']

    # Case2:    2D, temperature distribution and heat flow within a roof construction
    # Case3:    3D, temperature distribution and heat flows through the wall-balcony junction
    # Case4:    3D, temperature distribution and heat flows within a three dimensional thermal bridge consisting of an iron bar penetrating an insulation layer
    case2 ='/usr/share/feelpp/data/testcases/toolboxes/heat/cases/Building/ThermalBridgesENISO10211/case2.cfg'
    case3 = '/usr/share/feelpp/data/testcases/toolboxes/heat/cases/Building/ThermalBridgesENISO10211/case3.cfg'
    case4 ='/usr/share/feelpp/data/testcases/toolboxes/heat/cases/Building/ThermalBridgesENISO10211/case4.cfg'

    # Parametrisation
    case = parameter ([case2, case3, case4])
    nb_nodes = parameter([1,2,4,6])

    # Reference dictionary
    references = {
        'gaya': {'Execution_time': (0, None, None, 's')}
    }

    executable = 'feelpp_toolbox_heat'


    # mpiexec options
    @run_before('run')
    def set_launcher_options(self):
        self.job.launcher.options = ['-bind-to core', '--use-hwthread-cpus']


    @run_before('run')
    def set_task_number(self):
        self.num_tasks_per_node = 128     # 128 ou 256 ?   (=nb cpu ?)
        self.num_cpus_per_task = 1
        self.num_tasks = self.nb_nodes * self.num_tasks_per_node


    @run_before('run')
    def set_executable_opts(self):
        self.executable_opts = [f'--config-file {self.case}', '--heat.scalability-save=1']


    @performance_function('s', perf_key='Execution_time')
    def extract_execution_time(self):
        return sn.extractsingle(r'execution time\s+(\S+)s', self.stdout, 1, float)


    @run_before('performance')
    def set_perf_variables(self):
        self.perf_variables = {
            'Execution_time': self.extract_execution_time()
        }

    @sanity_function
    def check_finished(self):
        return sn.assert_found('[ Stopping Feel++ ]', self.stdout)
