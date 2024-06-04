import reframe                  as rfm
import reframe.utility.sanity   as sn
import reframe.core.runtime     as rt

import os


def parametrizeTaskNumber():
    for part in rt.runtime().system.partitions:
        nbTask = 1
        nbPhysicalCpus = part.processor.num_cpus_per_socket * part.processor.num_sockets
        while nbTask < nbPhysicalCpus:
            yield nbTask
            nbTask <<= 1

        nbNodes = part.devices[0].num_devices
        for i in range(1, nbNodes+1):
            nbTask = i*nbPhysicalCpus
            yield nbTask



@rfm.simple_test
class Setup(rfm.RunOnlyRegressionTest):

    valid_systems = ['local']
    valid_prog_environs = ['env_local']
    homeDir = os.environ['HOME']
    feelLogPath = os.path.join(homeDir, 'feelppdb/')


    # Parametrization
    nbTask = parameter(parametrizeTaskNumber())


    @run_before('run')
    def setTaskNumber(self):
        nbPhysicalCpus = self.current_partition.processor.num_cpus_per_socket * self.current_partition.processor.num_sockets
        self.num_tasks_per_node = min(self.nbTask, nbPhysicalCpus)
        self.num_cpus_per_task = 1
        self.num_tasks = self.nbTask


    # Launcher options
    @run_before('run')
    def set_launcher_options(self):
        self.job.launcher.options = ['-bind-to core']


    def meshPartionerCmd(self, nparts, ifile, odir, dim=3):
        return f'feelpp_mesh_partitioner --part {nparts} --ifile {ifile} --odir {odir} --dim {dim}'