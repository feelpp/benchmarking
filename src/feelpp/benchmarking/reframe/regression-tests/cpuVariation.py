from setup import *
import shutil


@rfm.simple_test
class ToolboxTest (Setup):

    descr = 'Launch testcases from the Heat Toolbox'
    toolbox = variable(str, value='')
    case = variable(str, value='')
    valuesPath = variable(str, value='')


    """ check what is needed """
    #checkers = variable(str, value='')             --> NEEDED
    #visualization = variable(str, value='')        --> DON'T THINK SO (complicated: use of export-scene-macro.py)
    #partitioning = variable(str, value='')         --> MAYBE


    @run_after('init')
    def setVariables(self):
        self.toolbox = self.config.Feelpp.toolbox
        self.case = self.config.Feelpp.CommandLine.configFilesToStr()


    @run_after('init')
    def buildPaths(self):
        self.feelOutputPrefix = os.path.join(self.config.Feelpp.CommandLine.repository.prefix, f"{self.toolbox}")
        self.feelOutputSuffix = os.path.join(self.config.Feelpp.CommandLine.repository.case, f'np_{self.nbTask}')
        self.feelOutputPath = os.path.join(self.feelOutputPrefix, f'{self.feelOutputSuffix}')
        self.valuesPath = os.path.join(self.feelOutputPath, f'{self.toolbox}.measures/values.csv')


    @run_before('run')
    def cleanFolder(self):
        if os.path.exists(self.feelOutputPath):
            print(" >>> Cleaning Feelpp output folder...")
            shutil.rmtree(self.feelOutputPath)
        else:
            print(" >>> New folder will be created...")


    @run_before('run')
    def set_executable_opts(self):

        self.executable = f'feelpp_toolbox_{self.toolbox}'
        self.executable_opts = [f'--config-files {self.case}',
                                f'--repository.prefix {self.feelOutputPrefix}',
                                f'--repository.case {self.feelOutputSuffix}',
                                '--repository.append.np 0',
                                '--fail-on-unknown-option 1']
                                #'--heat-fluid.json.patch=\'{ \"op\": \"replace\", \"path\": \"/Meshes/heatfluid/Import/filename\", \"value\": \"$cfgdir/meshpartitioning/' + str(meshIndex) + '/mesh_o_p$np.json\"} \' '
                                #      the previous option is for usePartitioning: True]

        if self.toolbox == 'heatfluid':
            scaleCommands = [   '--heat-fluid.scalability-save=1', '--heat-fluid.heat.scalability-save=1', '--heat-fluid.fluid.scalability-save=1']
        else:
            scaleCommands = [f'--{self.toolbox}.scalability-save=1']

        self.executable_opts.extend(scaleCommands)


    def buildScalePath(self, name):
        if self.toolbox == 'heatfluid':
            toolbox = 'heat-fluid'
            capitalized = 'HeatFluid'

        else:
            toolbox = self.toolbox
            capitalized = self.toolbox.capitalize()

        return os.path.join(self.feelOutputPath, f'{toolbox}.scalibility.{capitalized}{name}.data')


    @run_before('performance')
    def set_perf_vars(self):

        self.perf_variables = {}

        constructor_path = self.buildScalePath(name='Constructor')
        solve_path = self.buildScalePath(name='Solve')
        postprocessing_path = self.buildScalePath(name='PostProcessing')

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

        if self.toolbox == 'heatfluid':
            self.getHeatFluidValues()


    def getHeatFluidValues(self):
        fluid_constructor_path = os.path.join(self.feelOutputPath, 'heat-fluid.fluid.scalibility.FluidMechanicsConstructor.data')
        fluid_postprocessing_path = os.path.join(self.feelOutputPath, 'heat-fluid.fluid.scalibility.FluidMechanicsPostProcessing.data')
        heat_constructor_path = os.path.join(self.feelOutputPath, 'heat-fluid.heat.scalibility.HeatConstructor.data')
        heat_postprocessing_path = os.path.join(self.feelOutputPath, 'heat-fluid.heat.scalibility.HeatPostProcessing.data')

        fluid_constructor_names = self.get_column_names(fluid_constructor_path)
        fluid_postprocessing_names = self.get_column_names(fluid_postprocessing_path)
        heat_constructor_names = self.get_column_names(heat_constructor_path)
        heat_postprocessing_names = self.get_column_names(heat_postprocessing_path)

        length_fluid_constructor = len(fluid_constructor_names)
        length_fluid_postprocessing = len(fluid_postprocessing_names)
        length_heat_constructor = len(heat_constructor_names)
        length_heat_postprocessing = len(heat_postprocessing_names)

        fluid_constructor_line = self.extractLine(self.pattern_generator(length_fluid_constructor), fluid_constructor_path, length_fluid_constructor)
        fluid_postprocessing_line = self.extractLine(self.pattern_generator(length_fluid_postprocessing), fluid_postprocessing_path, length_fluid_postprocessing)
        heat_constructor_line = self.extractLine(self.pattern_generator(length_heat_constructor), heat_constructor_path, length_heat_constructor)
        heat_postprocessing_line = self.extractLine(self.pattern_generator(length_heat_postprocessing), heat_postprocessing_path, length_heat_postprocessing)

        make_perf = sn.make_performance_function

        for i in range(length_fluid_constructor):
            self.perf_variables.update( { 'F_' + fluid_constructor_names[i] : make_perf(fluid_constructor_line[i], 's')} )

        for i in range(length_fluid_postprocessing):
            self.perf_variables.update( { 'F_' + fluid_postprocessing_names[i] : make_perf(fluid_postprocessing_line[i], 's')} )

        for i in range(length_heat_constructor):
            self.perf_variables.update( { 'H_' + heat_constructor_names[i] : make_perf(heat_constructor_line[i], 's')} )

        for i in range(length_heat_postprocessing):
            self.perf_variables.update( { 'H_' + heat_postprocessing_names[i] : make_perf(heat_postprocessing_line[i], 's')} )


    @sanity_function
    def checkers_success(self):
        return sn.assert_not_found(r'\\32m \[failure\] ', self.stdout)