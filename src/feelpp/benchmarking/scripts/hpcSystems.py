from argparse import ArgumentParser
import os,json
from feelpp.benchmarking.reframe.config.configReader import JSONWithCommentsDecoder
from pathlib import Path

class HpcSystem:
    def __init__(
        self,
        runner,
        machine,
        partition = "",
        python_version = "",
        user_name = "",
        api_version =  "",
        account =  "",
        url =  "",
        submit =  ""
    ):
        self.runner = runner
        self.machine = machine
        self.partition = partition
        self.python_version = python_version
        self.user_name =  user_name
        self.api_version =  api_version
        self.account =  account
        self.url =  url
        self.submit =  submit

    def toDict(self):
        return self.__dict__

    def writeConfig(self,output_dir,machine_data):
        self.machine_cfg = os.path.join(output_dir,f"{self.machine}.json")
        self.reports_path = machine_data["reports_base_dir"]
        with open(self.machine_cfg,"w") as f:
            json.dump(machine_data,f)

    def createSumbitCommand(self):
        assert hasattr(self,"machine_cfg") and self.machine_cfg, "machine config path has not been set"

        self.submit_command = SubmissionCommandFactory.create(self.submit,self.machine)


class HpcSystemFactory:
    @staticmethod
    def dispatch(machine_name):
        if machine_name == "gaya":
            return HpcSystem( runner = "self-gaya", machine = "gaya", python_version = "3.10", user_name = "prudhomm", submit =  "cli" )
        elif machine_name == "discoverer":
            return HpcSystem( runner = "self-discoverer", machine = "discoverer", partition = "truePartition", python_version = "3.6", user_name = "vchabannes", submit = "cli" )
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
    parser.add_argument("--machine_output_dir", "-mod", required=True, type=str, help="path to folder where individual machine configs should be stored")
    args = parser.parse_args()

    if not os.path.exists(args.machine_output_dir):
        os.makedirs(args.machine_output_dir)

    with open(args.machine_config_path,"r") as f:
        machines = json.load(f,cls=JSONWithCommentsDecoder)

    matrix = []

    for machine_data in machines:
        hpc_system = HpcSystemFactory().dispatch(machine_data["machine"])
        hpc_system.writeConfig(args.machine_output_dir,machine_data)
        hpc_system.createSumbitCommand()
        matrix.append(hpc_system.toDict())


    print(matrix)
    return 0