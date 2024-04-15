import reframe as rfm
import reframe.utility.sanity as sn
import reframe.core.runtime as rt
import feelpp


@rfm.simple_test
class LaplacianTest(rfm.RunOnlyRegressionTest):
    num_threads = parameter([1,2,4,8,16,24])
    reference = {}
    #sourcesdir = './../../../src'
    valid_systems = ['*']
    valid_prog_environs = ['+openmp']
    #build_system = 'Make'

    executable = 'feelpp_toolbox_heat'
    executable_opts = ['--config-file /usr/share/feelpp/data/testcases/toolboxes/heat/cases/Building/ThermalBridgesENISO10211/case2.cfg']

    @run_before('run')
    def set_cpus_per_task(self):
        self.num_cpus_per_task = self.num_threads
        self.env_vars['OPM_NUM_THREADS'] = str(self.num_cpus_per_task)

    @run_after('setup')
    def skip_too_many(self):
        procinfo = self.current_partition.processor
        self.skip_if(self.num_threads > procinfo.num_cores, 'not enough cores')


    @sanity_function
    def assert_checkers(self):
        return sn.assert_found('[ Stopping Feel++ ]', self.stdout)
