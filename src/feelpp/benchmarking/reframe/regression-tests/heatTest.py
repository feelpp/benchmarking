import  reframe                 as rfm
import  reframe.utility.sanity  as sn


@rfm.simple_test
class HeatToolboxTest (rfm.RunOnlyRegressionTest):

    # Initialisation
    descr = 'Launch testcases from the Heat Toolbox'
    valid_systems = ['gaya']
    valid_prog_environs = ['env_gaya']
    executable = 'feelpp_toolbox_heat'

    # Case2:    2D, temperature distribution and heat flow within a roof construction
    # Case3:    3D, temperature distribution and heat flows through the wall-balcony junction
    # Case4:    3D, temperature distribution and heat flows within a three dimensional thermal bridge consisting of an iron bar penetrating an insulation layer
    case3 = '/home/u4/csmi/2023/pierre/Projet/reframeLocal/modified_cases/case3.cfg'


    # Parametrisation
    case = parameter ([case3])  # , ..., more cases to be added])
    nb_nodes = parameter([1,2,4,6])


    # mpiexec options
    @run_before('run')
    def set_launcher_options(self):
        self.job.launcher.options = ['-bind-to core']


    @run_before('run')
    def set_task_number(self):
        self.num_tasks_per_node = 128
        self.num_cpus_per_task = 1
        self.num_tasks = self.nb_nodes * self.num_tasks_per_node



    @run_before('run')
    def set_executable_opts(self):
        self.executable_opts = [f'--config-file {self.case}', '--heat.scalability-save=1']


    # Scalability performances
    #       constructor:    8 values
    #       solve:          3 values
    #       postprocessing: 1 value

    name_patt = '([a-zA-z]\-]+)'
    val_patt  = '([0-9e\-\+\.]+)'

    @run_after('run')
    def get_constructor_names(self, index=1):
        return sn.extractsingle(rf'nProc[\s]+{self.name_patt}[\s]+{self.name_patt}[\s]+{self.name_patt}[\s]+{self.name_patt}[\s]+{self.name_patt}[\s]+{self.name_patt}[\s]+{self.name_patt}[\s]+{self.name_patt}[\s]+',
                                '/home/u4/csmi/2023/pierre/feelppdb/toolboxes/heat/ThermalBridgesENISO10211/Case3_modified/heat.scalibility.HeatConstructor.data',
                                index, str)

    @run_after('run')
    def get_solve_names(self, index=1):
        return sn.extractsingle(rf'nProc[\s]+{self.name_patt}[\s]+{self.name_patt}[\s]+{self.name_patt}[\s]+{self.name_patt}[\s]+',
                                '/home/u4/csmi/2023/pierre/feelppdb/toolboxes/heat/ThermalBridgesENISO10211/Case3_modified/heat.scalibility.HeatSolve.data',
                                index, str)

    @run_after('run')
    def get_postprocessing_names(self, index=1):
        return sn.extractsingle(rf'nProc[\s]+{self.name_patt}[\s]+',
                                '/home/u4/csmi/2023/pierre/feelppdb/toolboxes/heat/ThermalBridgesENISO10211/Case3_modified/heat.scalibility.HeatPostProcessing.data',
                                index, str)

    @performance_function('s')
    def extract_constructor_scale(self, index=1):
        return sn.extractsingle(rf'{self.num_tasks}[\s]+{self.val_patt}[\s]+{self.val_patt}[\s]+{self.val_patt}[\s]+{self.val_patt}[\s]+{self.val_patt}[\s]+{self.val_patt}[\s]+{self.val_patt}[\s]+{self.val_patt}[\s]+',
                                '/home/u4/csmi/2023/pierre/feelppdb/toolboxes/heat/ThermalBridgesENISO10211/Case3_modified/heat.scalibility.HeatConstructor.data',
                                index, float)

    @performance_function('s')
    def extract_solve_scale(self, index=1):
        return sn.extractsingle(rf'{self.num_tasks}[\s]+{self.val_patt}[\s]+{self.val_patt}[\s]+{self.val_patt}[\s]+{self.val_patt}[\s]+',
                                '/home/u4/csmi/2023/pierre/feelppdb/toolboxes/heat/ThermalBridgesENISO10211/Case3_modified/heat.scalibility.HeatConstructor.data',
                                index, float)


    @performance_function('s')
    def extract_postprocessing_scale(self, index=1):
        return sn.extractsingle(rf'{self.num_tasks}[\s]+{self.val_patt}[\s]+',
                                '/home/u4/csmi/2023/pierre/feelppdb/toolboxes/heat/ThermalBridgesENISO10211/Case3_modified/heat.scalibility.HeatConstructor.data',
                                index, float)

    """
    @run_before('performance')
    def set_perf_vars(self):
        self.perf_variables = {}

        for ind in range(1,9):
            self.perf_variables.update( {self.get_constructor_names() : self.extract_constructor_scale(index=ind)} )

        for ind in range(2,5):
            self.perf_variables.update( {self.get_solve_names() : self.extract_solve_scale(index=ind)} )

        for ind in range(1,2):
            self.perf_variables.update( {self.get_postprocessing_names() : self.extract_postprocessing_scale(index=ind)} )
    """

    @sanity_function
    def checkers_success(self):
        return sn.assert_not_found(r'\\32m [failure] ', self.stdout)