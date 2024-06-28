from setup import *
import reframe.utility.sanity as sn


@rfm.simple_test
class HeatToolboxTest (Setup):

    descr = 'Launch testcases from the Heat Toolbox'
    toolbox = 'heat'
    #toolbox = variable(str)
    case = variable(str)


    @run_after('init')
    def build_paths(self):
        self.caseRelativeDir = self.case.split("cases/")[-1][:-4]
        self.feelOutputPath = os.path.join(self.feelppdbPath, f'toolboxes/{self.toolbox}/{self.caseRelativeDir}_np{self.nbTask}')

    @run_before('run')
    def set_executable_opts(self):
        self.executable = f'feelpp_toolbox_{self.toolbox}'
        self.executable_opts = [f'--config-file {self.case}',
                                f'--repository.prefix {self.feelppdbPath}',
                                f'--repository.case {self.feelOutputPath}',
                                '--repository.append.np 0',
                                '--heat.scalability-save 1']
                                #'--case.discretization PXXX'


    namePatt = '([a-zA-z\-]+)'
    valPatt  = '([0-9e\-\+\.]+)'


    def get_constructor_name(self, index=1):
        scalePath = os.path.join(self.feelOutputPath, f'{self.toolbox}.scalibility.{self.toolbox.capitalize()}Constructor.data')
        return sn.extractsingle(rf'nProc[\s]+{self.namePatt}[\s]+{self.namePatt}[\s]+{self.namePatt}[\s]+{self.namePatt}[\s]+{self.namePatt}[\s]+{self.namePatt}[\s]+{self.namePatt}[\s]+{self.namePatt}[\s]+',
                                scalePath, index, str)


    def get_solve_name(self, index=1):
        scalePath = os.path.join(self.feelOutputPath, f'{self.toolbox}.scalibility.{self.toolbox.capitalize()}Solve.data')
        return sn.extractsingle(rf'nProc[\s]+{self.namePatt}[\s]+{self.namePatt}[\s]+{self.namePatt}[\s]+{self.namePatt}',
                                scalePath, index, str)


    def get_postprocessing_name(self, index=1):
        scalePath = os.path.join(self.feelOutputPath, f'{self.toolbox}.scalibility.{self.toolbox.capitalize()}PostProcessing.data')
        return sn.extractsingle(rf'nProc[\s]+{self.namePatt}[\s]+',
                                scalePath, index, str)


    @performance_function('s')
    def extract_constructor_scale(self, index=1):
        scalePath = os.path.join(self.feelOutputPath, f'{self.toolbox}.scalibility.{self.toolbox.capitalize()}Constructor.data')
        return sn.extractsingle(rf'^{self.num_tasks}[\s]+{self.valPatt}[\s]+{self.valPatt}[\s]+{self.valPatt}[\s]+{self.valPatt}[\s]+{self.valPatt}[\s]+{self.valPatt}[\s]+{self.valPatt}[\s]+{self.valPatt}[\s]+',
                                scalePath, index, float)


    @performance_function('s')
    def extract_solve_scale(self, index=1):
        scalePath = os.path.join(self.feelOutputPath, f'{self.toolbox}.scalibility.{self.toolbox.capitalize()}Solve.data')
        # the first value to extract is ksp-niter, integer
        valType = float if (index!=1) else int
        return sn.extractsingle(rf'^{self.num_tasks}[\s]+{self.valPatt}[\s]+{self.valPatt}[\s]+{self.valPatt}[\s]+{self.valPatt}',
                                scalePath, index, valType)


    @performance_function('s')
    def extract_postprocessing_scale(self, index=1):
        scalePath = os.path.join(self.feelOutputPath, f'{self.toolbox}.scalibility.{self.toolbox.capitalize()}PostProcessing.data')
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