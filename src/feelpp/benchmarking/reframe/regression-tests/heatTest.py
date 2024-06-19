from setup import *
import reframe.utility.sanity as sn


@rfm.simple_test
class HeatToolboxTest (Setup):

    descr = 'Launch testcases from the Heat Toolbox'
    executable = 'feelpp_toolbox_heat'
    case = variable(str)


    @run_after('init')
    def readCfg(self):
        with open(self.case, 'r') as file:
            for line in file:
                if line.startswith('directory'):
                    outputDir = line.split('=')[1].strip()
                if line.startswith('json.filename'):
                    geoPath = line.split('=')[1].strip()
                    geoPath = geoPath.replace('.json', '.geo')
                if line.startswith('case.dimension'):
                    dim = line.split('=')[1].strip()

        self.feelLogPath = os.path.join(self.feelLogPath, outputDir)
        self.geoPath = geoPath
        self.dim = dim


    @run_before('run')
    def set_executable_opts(self):
        filename = os.path.basename(self.case).replace('-bench.cfg', f'_p{self.num_tasks}.json')
        filePath = os.path.join(self.partitionDir, filename)
        self.executable_opts = [f'--config-file={self.case}',
                                f'--heat.filename={filePath}',
                                '--heat.scalability-save=1']


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