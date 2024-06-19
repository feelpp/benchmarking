import reframe                  as rfm
import reframe.core.runtime     as rt

import os

def parametrizeTaskNumber():
    for part in rt.runtime().system.partitions:
        nbTask = 1
        while nbTask < part.processor.num_cpus:
            yield nbTask
            nbTask <<= 1

        nbNodes = part.devices[0].num_devices
        for i in range(1, nbNodes+1):
            nbTask = i * part.processor.num_cpus
            yield nbTask



@rfm.simple_test
class Setup(rfm.RunOnlyRegressionTest):

    valid_systems = ['*']
    valid_prog_environs = ['*']

    #TODO
    homeDir = os.environ['HOME']
    feelLogPath = os.path.join(homeDir, 'feelppdb/')


    # Parametrization
    nbTask = parameter(parametrizeTaskNumber())
    #nbTask = parameter([4,8])


    @run_before('run')
    def setTaskNumber(self):
        self.num_tasks_per_node = min(self.nbTask, self.current_partition.processor.num_cpus)
        self.num_cpus_per_task = 1
        self.num_tasks = self.nbTask


    # Launcher options
    @run_before('run')
    def set_launcher_options(self):
        self.job.launcher.options = ['-bind-to core']