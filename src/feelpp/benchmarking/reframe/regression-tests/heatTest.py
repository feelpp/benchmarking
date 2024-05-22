import  reframe                 as rfm
import  reframe.utility.sanity  as sn
import os


@rfm.simple_test
class HeatToolboxTest (rfm.RunOnlyRegressionTest):

    def __init__(self):
        super().__init__()
        self.feelLogPath = self.build_feel_path()

    # Initialisation
    descr = 'Launch testcases from the Heat Toolbox'
    valid_systems = ['gaya']
    valid_prog_environs = ['env_gaya']

    heatCasesPath = '/usr/share/feelpp/data/testcases/toolboxes/heat/cases/'

    # 3d, temperature distribution and heat flows through the wall-balcony junction
    case3 = 'Building/ThermalBridgesENISO10211/case3.cfg'

    # Parametrization
    case = parameter ([case3])      # more cases to be added...
    nbNodes = parameter([2,4,6,8])

    homeDir = os.environ['HOME']

    def build_feel_path(self):
        caseModif = self.case.replace('case3.cfg', 'Case3')
        caseModif = caseModif.replace('Building/', '')
        feelLogPath = os.path.join(self.homeDir, 'feelppdb/toolboxes/heat', caseModif)
        return feelLogPath


    # Launcher options
    @run_before('run')
    def set_launcher_options(self):
        self.job.launcher.options = ['-bind-to core', '--use-hwthread-cpus']

    @run_before('run')
    def set_task_number(self):
        self.num_tasks_per_node = 128
        self.num_cpus_per_task = 1
        self.num_tasks = self.nbNodes * self.num_tasks_per_node


    # Executable options
    executable = 'feelpp_toolbox_heat'

    @run_before('run')
    def set_executable_opts(self):
        fullPath = os.path.join(self.heatCasesPath, self.case3)
        self.executable_opts = [f'--config-file {fullPath}',
                                '--case.discretization P1',
                                '--heat.scalability-save 1']


    # Performance variables extraction using regex patterns
    namePatt = '([a-zA-z\-]+)'
    valPatt  = '([0-9e\-\+\.]+)'

    @sn.deferrable
    def get_constructor_name(self, index=1):
        scalePath = os.path.join(self.feelLogPath, 'heat.scalibility.HeatConstructor.data')
        return sn.extractsingle(rf'nProc[\s]+{self.namePatt}[\s]+{self.namePatt}[\s]+{self.namePatt}[\s]+{self.namePatt}[\s]+{self.namePatt}[\s]+{self.namePatt}[\s]+{self.namePatt}[\s]+{self.namePatt}[\s]+',
                                scalePath, index, str)

    @sn.deferrable
    def get_solve_name(self, index=1):
        scalePath = os.path.join(self.feelLogPath, 'heat.scalibility.HeatSolve.data')
        return sn.extractsingle(rf'nProc[\s]+{self.namePatt}[\s]+{self.namePatt}[\s]+{self.namePatt}[\s]+{self.namePatt}',
                                scalePath, index, str)

    @sn.deferrable
    def get_postprocessing_name(self, index=1):
        scalePath = os.path.join(self.feelLogPath, 'heat.scalibility.HeatPostProcessing.data')
        return sn.extractsingle(rf'nProc[\s]+{self.namePatt}[\s]+',
                                scalePath, index, str)

    @performance_function('s')
    def extract_constructor_scale(self, index=1):
        scalePath = os.path.join(self.feelLogPath, 'heat.scalibility.HeatConstructor.data')
        return sn.extractsingle(rf'^{self.num_tasks}[\s]+{self.valPatt}[\s]+{self.valPatt}[\s]+{self.valPatt}[\s]+{self.valPatt}[\s]+{self.valPatt}[\s]+{self.valPatt}[\s]+{self.valPatt}[\s]+{self.valPatt}[\s]+',
                                scalePath, index, float)

    @performance_function('s')
    def extract_solve_scale(self, index=1):
        scalePath = os.path.join(self.feelLogPath, 'heat.scalibility.HeatSolve.data')
        # the first value to extract is ksp-niter, integer
        valType = float if (index!=1) else int
        return sn.extractsingle(rf'^{self.num_tasks}[\s]+{self.valPatt}[\s]+{self.valPatt}[\s]+{self.valPatt}[\s]+{self.valPatt}',
                                scalePath, index, valType)

    @performance_function('s')
    def extract_postprocessing_scale(self, index=1):
        scalePath = os.path.join(self.feelLogPath, 'heat.scalibility.HeatPostProcessing.data')
        return sn.extractsingle(rf'^{self.num_tasks}[\s]+{self.valPatt}',
                                scalePath, index, float)


    @run_before('performance')
    def set_perf_vars(self):
        self.perf_variables = {}

        # 8 values to extract
        for i in range(1,9):
            self.perf_variables.update( {str(self.get_constructor_name(i)) : self.extract_constructor_scale(i)} )
        # 4 values to extract
        for i in range(1,5):
            self.perf_variables.update( {str(self.get_solve_name(i)) : self.extract_solve_scale(i)} )
        # 1 value to extract
        for i in range(1,2):
            self.perf_variables.update( {str(self.get_postprocessing_name(i)) : self.extract_postprocessing_scale(i)} )


    @sanity_function
    def checkers_success(self):
        return sn.assert_not_found(r'\\32m [failure] ', self.stdout)