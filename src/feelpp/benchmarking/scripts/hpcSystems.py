from argparse import ArgumentParser
import os,json
from feelpp.benchmarking.reframe.config.configReader import JSONWithCommentsDecoder
from pathlib import Path

class HpcSystem:
    def __init__(self):
        self.runner = ""
        self.machine = ""
        self.python_version = ""
        self.user_name = ""
        self.api_version =  ""
        self.user_name =  ""
        self.account =  ""
        self.url =  ""
        self.submit =  ""

    def toJson(self):
        return json.dumps(self.__dict__)

    def writeConfig(self,output_dir,machine_data):
        self.machine_cfg = os.path.join(output_dir,f"{self.machine}.json")
        with open(self.machine_cfg,"w") as f:
            json.dump(machine_data,f)

    def createSumbitCommand(self, benchmark_config_path, plots_config_path, move_results):
        assert hasattr(self,"machine_cfg") and self.machine_cfg, "machine config path has not been set"

        self.submit_command = SubmissionCommandFactory.create(self.submit,self.machine,[
            f"--matrix-config {self.machine_cfg} ",
            f"--benchmark-config {benchmark_config_path} ",
            f"--plots-config {plots_config_path} ",
            f"--move-results {move_results}"
        ])

class Gaya(HpcSystem):
    def __init__(self):
        super().__init__()
        self.runner = "self-gaya"
        self.machine = "gaya"
        self.python_version = "3.10"
        self.user_name = "prudhomm"
        self.submit =  "cli"

class Discoverer(HpcSystem):
    def __init__(self):
        super().__init__()
        self.runner = "self-discoverer"
        self.machine = "discoverer"
        self.partition = "truePartition"
        self.python_version = "3.6"
        self.user_name = "vchabannes"
        self.submit = "cli"


class HpcSystemFactory:
    @staticmethod
    def dispatch(machine_name):
        if machine_name == "gaya":
            return Gaya()
        elif machine_name == "discoverer":
            return Discoverer()
        else:
            raise ValueError(f"HPC resource {machine_name} not found...")



class JobSubmission:
    def __init__(self,machine):
        self.executable = None
        self.script = f"./src/feelpp/benchmarking/reframe/config/machineConfigs/{machine}.sh"

    def buildCommand(self, options):
        pass

class Cli(JobSubmission):
    def __init__(self,machine):
        super().__init__(machine)
        self.executable = "bash"

    def buildCommand(self, options):
        return " ".join([self.executable, self.script] + options)

class SubmissionCommandFactory:
    @staticmethod
    def create(submit,machine,options):
        if submit == "cli":
            return Cli(machine).buildCommand(options)
        else:
            raise ValueError(f"{submit} is not supported")

def hpcSystemDispatcher_cli():
    parser = ArgumentParser()
    parser.add_argument("--machine_config_path", "-mcp", required=True, type=str, help="path to the machines config json")
    parser.add_argument("--benchmark_config_path", "-bcp", required=True, type=str, help="path to the benchmark config json")
    parser.add_argument("--plots_config_path", "-pcp", required=True, type=str, help="path to the plots config json")
    parser.add_argument("--machine_output_dir", "-mod", required=True, type=str, help="path to folder where individual machine configs should be stored")
    parser.add_argument("--move_results", "-mv", required=True, type=str, help="path to move the results to")
    args = parser.parse_args()

    if not os.path.exists(args.machine_output_dir):
        os.makedirs(args.machine_output_dir)

    with open(args.machine_config_path,"r") as f:
        machines = json.load(f,cls=JSONWithCommentsDecoder)

    matrix = []

    for machine_data in machines:
        hpc_system = HpcSystemFactory().dispatch(machine_data["machine"])
        hpc_system.writeConfig(args.machine_output_dir,machine_data)
        hpc_system.createSumbitCommand(
            args.benchmark_config_path,
            args.plots_config_path,
            args.move_results
        )
        matrix.append(hpc_system.toJson())


    print(matrix)
    return 0