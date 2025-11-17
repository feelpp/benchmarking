from argparse import ArgumentParser
import glob, json, copy, os
from feelpp.benchmarking.dashboardRenderer.handlers.girder import GirderHandler

def mergeDicts(dict1, dict2):
    """Recursively merges two dictionaries."""
    merged = copy.deepcopy(dict1)  # Make a deep copy of the first dictionary
    for key, value in dict2.items():
        if key in merged:
            if not value: continue

            if isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = mergeDicts(merged[key], value)
            elif isinstance(merged[key], list) and isinstance(value, list):
                merged[key] = list(set(merged[key] + value))
            else:
                merged[key] = value
        else:
            merged[key] = value
    return merged




def jsonConfigMerge_cli():
    """ Merge multiple json files into a single one"""
    parser = ArgumentParser()
    parser.add_argument("--file_pattern", '-fp', required = True, type=str, help="File glob pattern of the json files to merge")
    parser.add_argument("--output_file_path","-o",required=True,type=str,help="Path of the resulting file to be saved to")
    parser.add_argument("--update_paths", "-u", action="store_true", help="Whether to update the config file paths")
    args = parser.parse_args()

    master_config = {}
    for filename in glob.glob(args.file_pattern,recursive=True):
        with open(filename,"r") as f:
            current_config = json.load(f)

        if args.update_paths:
            file_dirpath = os.path.dirname(os.path.relpath(filename,"."))
            report_paths = glob.glob(os.path.join(file_dirpath,"**","reframe_report.json"),recursive=True)
            for report in report_paths:
                app,use_case,machine = report.split("/")[-5:-2]

                current_config["execution_mapping"][app][machine][use_case]["path"] = os.path.join(file_dirpath,app,use_case,machine)

        master_config = mergeDicts(master_config,current_config)

    with open(args.output_file_path,"w") as f:
        f.write(json.dumps(master_config))

    return 0


def updateStageConfig_cli():
    """Upload new staged benchmarks to production and update production config"""
    parser = ArgumentParser()
    parser.add_argument("--stage_config", '-stag', required = True, type=str, help="File path of the stage configuration file")
    parser.add_argument("--production_config","-prod",required=True,type=str,help="FIle path of the production configuration file")
    parser.add_argument("--production_girder_id", "-prodid", required=True,type=str, help="Girder id of the production folder")
    args = parser.parse_args()

    with open(args.stage_config,"r") as f:
        stage_cfg = json.load(f)
    with open(args.production_config,"r") as f:
        prod_cfg = json.load(f)

    girder_client = GirderHandler(None)

    for app_name, machines in stage_cfg["execution_mapping"].items():
        for machine_name, use_cases in machines.items():
            for use_case_name, info in use_cases.items():
                stage_platform = info["platform"]
                stage_path = info["path"]

                if (
                    app_name in prod_cfg["execution_mapping"] and
                    machine_name in prod_cfg["execution_mapping"][app_name] and
                    use_case_name in prod_cfg["execution_mapping"][app_name][machine_name]
                ):
                    prod_info = prod_cfg["execution_mapping"][app_name][machine_name][use_case_name]
                    prod_platorm = prod_info["platform"]
                    prod_path = prod_info["path"]

                    if stage_platform == "local":
                        for report_item_basename in os.listdir(stage_path):
                            girder_client.upload( os.path.join(stage_path,report_item_basename), prod_path, reuse_existing=False)
                        stage_cfg["execution_mapping"][app_name][machine_name][use_case_name]["path"] = prod_path
                        stage_cfg["execution_mapping"][app_name][machine_name][use_case_name]["platform"] = prod_platorm
                    else:
                        raise ValueError("Unexpected: non local path but benchmark is staged")

                else:
                    print(f"{app_name}-{machine_name}-{use_case_name} not found in production... Adding it.")

                    tmp_location = os.path.join("./tmp",f"{app_name}_{use_case_name}_{machine_name}")
                    os.rename(stage_path,tmp_location)
                    uploaded_id = girder_client.upload( tmp_location, args.production_girder_id, return_id=True )

                    stage_cfg["execution_mapping"][app_name][machine_name][use_case_name]["path"] = uploaded_id
                    stage_cfg["execution_mapping"][app_name][machine_name][use_case_name]["platform"] = "girder"

    with open(args.stage_config,"w") as f:
        json.dump(stage_cfg,f)

    return 0