from setup import *
import reframe.utility.sanity as sn


@rfm.simple_test
class HeatToolboxTest (Setup):
    descr = 'Launch testcases from the Heat Toolbox'
    toolbox = 'heat'
    #toolbox = variable(str)
    case = variable(str)

    checkers = variable(str, value='')
    visualization = variable(str, value='')
    partitioning = variable(str, value='')


    @run_after('init')
    def build_paths(self):
        self.caseRelativeDir = self.case.split("cases/")[-1][:-4]
        self.feelOutputPath = os.path.join(self.feelppdbPath, f'toolboxes/{self.toolbox}/{self.caseRelativeDir}_np{self.nbTask}')
        self.relativeOutputPath = self.feelOutputPath.split("benchmarking/")[-1]

        self.checkers = os.path.join(self.feelOutputPath, f'{self.toolbox}.measures/values.csv')
        self.visualization = os.path.join(self.feelOutputPath, f'{self.toolbox}.exports/Export.case')
        self.partitioning = os.path.join(self.feelOutputPath, f'{self.toolbox}.mesh.json')

    @run_before('run')
    def set_executable_opts(self):
        self.executable = f'feelpp_toolbox_{self.toolbox}'
        self.executable_opts = [f'--config-files {self.case}',
                                f'--repository.prefix {self.feelppdbPath}',
                                f'--repository.case {self.relativeOutputPath}',
                                '--repository.append.np 0',
                                '--heat.scalability-save 1',
                                '--fail-on-unknown-option 1']
                                #'--case.discretization PXXX'


    """
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
    """

    # Capture patterns
    namePatt = '([a-zA-z\-]+)'
    valPatt  = '([0-9e\-\+\.]+)'

    def get_column_names(self, filename):
        with open(filename, 'r') as file:
            for line in file:
                if line.startswith('# nProc'):
                    header = line.strip().split()
                    return header[2:]               # exclude '# nProc'
        return []


    def pattern_generator(self, valuesNumber):
        valPattern = '([0-9e\-\+\.]+)'
        linePattern = r'^\d+[\s]+' + rf'{valPattern}[\s]+' * valuesNumber
        return linePattern[:-1] + '*'

    def extractLine(self, pattern, path, line):
        return sn.extractall(pattern, path, conv=float)


    @run_before('performance')
    def set_perf_vars(self):

        self.perf_variables = {}

        constructor_path = f'{self.toolbox}.scalibility.{self.toolbox.capitalize()}Constructor.data'
        solve_path = f'{self.toolbox}.scalibility.{self.toolbox.capitalize()}Solve.data'
        postprocessing_path = f'{self.toolbox}.scalibility.{self.toolbox.capitalize()}PostProcessing.data'

        constructor_names = self.get_column_names(constructor_path)
        solve_names = self.get_column_names(solve_path)
        postprocessing_names = self.get_column_names(postprocessing_path)

        constructor_line = self.extractLine(self.pattern_generator(len(constructor_names)), constructor_path)
        solve_line = self.extractLine(self.pattern_generator(len(solve_names)), solve_path)
        postprocessing_line = self.extractLine(self.pattern_generator(len(postprocessing_names)), postprocessing_path)


        for i in range(1, len(constructor_names)):
            self.perf_variables.update( {str(constructor_names[i]) : constructor_line[i]} )

        for i in range(1, len(solve_names)):
            self.perf_variables.update( {str(solve_names[i]) : solve_line[i]} )

        for i in range(1, len(postprocessing_names)):
            self.perf_variables.update( {str(postprocessing_names[i]) : postprocessing_line[i]} )


    @sanity_function
    def checkers_success(self):
        return sn.assert_not_found(r'\\32m [failure] ', self.stdout)