from setup import *

@rfm.simple_test
class ToolboxTest (Setup):

    descr = 'Launch testcases from the Heat Toolbox'
    toolbox = variable(str, value=os.getenv('TOOLBOX'))
    case = variable(str, value=os.getenv('FEELPP_CFG_PATHS'))

    #checkers = variable(str, value='')
    #visualization = variable(str, value='')
    #partitioning = variable(str, value='')

    @run_after('init')
    def build_paths(self):
        """ self.feelpp_out_prefix = self.feelppdbPath """

        parentDir = os.path.basename(os.path.dirname(self.case))
        caseNoExt = os.path.basename(self.case)[:-4]

        self.caseRelativeDir = self.case.split("cases/")[-1][:-4]
        self.feelOutputPath = os.path.join(self.feelppdbPath, f'{self.toolbox}/{parentDir}/{caseNoExt}/np{self.nbTask}')


        print(" > self.caseRelativeDir:\t", self.caseRelativeDir)
        print(" > self.feelpp_output_prefix:\t", self.feelpp_out_prefix)
        print(" > self.feelOutputPath:\t\t", self.feelOutputPath)
        print("")

        #self.checkers = os.path.join(self.feelOutputPath, f'{self.toolbox}.measures/values.csv')
        #self.visualization = os.path.join(self.feelOutputPath, f'{self.toolbox}.exports/Export.case')
        #self.partitioning = os.path.join(self.feelOutputPath, f'{self.toolbox}.mesh.json')


    @run_before('run')
    def set_executable_opts(self):
        self.executable = f'feelpp_toolbox_{self.toolbox}'
        self.executable_opts = [f'--config-files {self.case}',
                                f'--repository.prefix {self.feelppdbPath}', # --> to export
                                f'--repository.case {self.relativeOutputPath}', # --> to export
                                '--repository.append.np 0',
                                '--heat.scalability-save 1',
                                '--fail-on-unknown-option 1']
        # --heat.json.merge_patch={"Meshes":{"heat":{"Import":{"hsize": 0.01}}}}


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




    @run_before('performance')
    def set_perf_vars(self):

        self.perf_variables = {}

        constructor_path = os.path.join(self.feelOutputPath, f'{self.toolbox}.scalibility.{self.toolbox.capitalize()}Constructor.data')
        solve_path = os.path.join(self.feelOutputPath, f'{self.toolbox}.scalibility.{self.toolbox.capitalize()}Solve.data')
        postprocessing_path = os.path.join(self.feelOutputPath, f'{self.toolbox}.scalibility.{self.toolbox.capitalize()}PostProcessing.data')

        constructor_names = self.get_column_names(constructor_path)
        solve_names = self.get_column_names(solve_path)
        postprocessing_names = self.get_column_names(postprocessing_path)

        lengthConstructor = len(constructor_names)
        lengthSolve = len(solve_names)
        lengthPostproc = len(postprocessing_names)

        constructor_line = self.extractLine(self.pattern_generator(lengthConstructor), constructor_path, lengthConstructor)
        solve_line = self.extractLine(self.pattern_generator(lengthSolve), solve_path, lengthSolve)
        postprocessing_line = self.extractLine(self.pattern_generator(lengthPostproc), postprocessing_path, lengthPostproc)

        make_perf = sn.make_performance_function

        for i in range(lengthConstructor):
            self.perf_variables.update( {constructor_names[i] : make_perf(constructor_line[i], 's')} )

        for i in range(lengthSolve):            # 1st performance is ksp-niter
            unit = 's' if i!=0 else 'iteration'
            self.perf_variables.update( {solve_names[i] : make_perf(solve_line[i], unit)} )

        for i in range(lengthPostproc):
            self.perf_variables.update( {postprocessing_names[i] : make_perf(postprocessing_line[i], 's')} )


    @sanity_function
    def checkers_success(self):
        return sn.assert_not_found(r'\\32m \[failure\] ', self.stdout)