from argparse import ArgumentParser
import os,json
from feelpp.benchmarking.reframe.config.configReader import JSONWithCommentsDecoder

def parseHpcSystems_cli():

    runners = {
        "meluxina": {
            "runner": "self-meluxina",
            "machine": "meluxina",
            "partition": "truePartition",
            "python_version": "3.6",
            "api_version": "v0.0.38",
            "user_name": "u101096",
            "account": "p200229",
            "url": "http://slurmrestd.meluxina.lxp.lu:6820",
            "submit": "rest"
        },
        "gaya":{
            "runner": "self-gaya",
            "machine": "gaya",
            "partition": "truePartition",
            "python_version": "3.10",
            "api_version": "",
            "user_name": "prudhomm",
            "account": "",
            "url": "",
            "submit": "cli"
        },
        "lumi":{
            "runner": "self-lumi",
            "machine": "lumi",
            "partition": "truePartition",
            "python_version": "3.6",
            "api_version": "",
            "user_name": "prudhomm",
            "account": "",
            "url": "",
            "submit": "sbatch"
        },
        "discoverer":{
            "runner": "self-discoverer",
            "machine": "discoverer",
            "partition": "truePartition",
            "python_version": "3.6",
            "api_version": "",
            "user_name": "vchabannes",
            "account": "",
            "url": "",
            "submit": "cli"
        },
        "karolina":{
            "runner": "self-karolina",
            "machine": "karolina",
            "partition": "truePartition",
            "python_version": "3.6",
            "api_version": "",
            "user_name": "vchabannes",
            "account": "",
            "url": "",
            "submit": "cli"
        }
    }

    parser = ArgumentParser()
    parser.add_argument("--machine_config_path", "-mp", required=True, type=str, help="path to the machines config json")
    parser.add_argument("--output_dir", "-o", required=True, type=str, help="path to folder where individual machine configs should be stored")
    args = parser.parse_args()

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    with open(args.machine_config_path,"r") as f:
        machines = json.load(f,cls=JSONWithCommentsDecoder)

    matrix = []

    for machine_data in machines:
        if machine_data["machine"] not in runners:
            raise ValueError(f"{machine_data['machine']} not found in runner mapping")

        machine_config_path = os.path.join(args.output_dir,f"{machine_data['machine']}.json")
        with open(machine_config_path,"w") as f:
            json.dump(machine_data,f)

        runner_info = runners[machine_data["machine"]]
        runner_info["machine_cfg"] = os.path.abspath(machine_config_path)
        matrix.append(runner_info)


    print(matrix)
    return 0