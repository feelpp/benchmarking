from argparse import ArgumentParser
import glob, json,  os, shutil
from feelpp.benchmarking.dashboardRenderer.handlers.girder import GirderHandler
from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import DashboardSchema


def jsonConfigMerge_cli():
    """ Merge multiple json files into a single one"""
    parser = ArgumentParser()
    parser.add_argument("--file_pattern", '-fp', required = True, type=str, help="File glob pattern of the json files to merge")
    parser.add_argument("--output_file_path","-o",required=True,type=str,help="Path of the resulting file to be saved to")
    parser.add_argument("--update_paths", "-u", action="store_true", help="Whether to update the config file paths")
    args = parser.parse_args()

    for i,filename in enumerate(glob.glob(args.file_pattern,recursive=True)):
        with open(filename,"r") as f:
            current_config = json.load(f)
        current_config = DashboardSchema.model_validate( current_config )
        if i == 0:
            master_config = current_config.model_copy()
        if args.update_paths:
            file_dirpath = os.path.dirname(os.path.relpath(filename,"."))
            report_paths = glob.glob(os.path.join(file_dirpath,"**","reframe_report.json"),recursive=True)
            for report in report_paths:
                app,use_case,machine = report.split("/")[-5:-2]
                order_map = {
                    "applications":app,
                    "machines":machine,
                    "use_cases":use_case
                }

                curr = current_config.component_map.mapping
                for order in current_config.component_map.component_order:
                    curr = curr[order_map[order]]
                curr["path"] = os.path.join(file_dirpath,app,use_case,machine)
        master_config.merge(current_config)

    with open(args.output_file_path,"w") as f:
        f.write(json.dumps(master_config.model_dump()))

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
    stage_cfg = DashboardSchema.model_validate(stage_cfg)
    with open(args.production_config,"r") as f:
        prod_cfg = json.load(f)
    prod_cfg = DashboardSchema.model_validate(prod_cfg)

    girder_client = GirderHandler(None)

    #TODO: Use recursion to support arbitrary lvls
    for level_1_name, level_1 in stage_cfg.component_map.mapping.items():
        for level_2_name, level_2 in level_1.items():
            for level_3_name, info in level_2.items():
                stage_platform = info["platform"]
                stage_path = info["path"]

                if (
                    level_1_name in prod_cfg.component_map.mapping and
                    level_2_name in prod_cfg.component_map.mapping[level_1_name] and
                    level_3_name in prod_cfg.component_map.mapping[level_1_name][level_2_name]
                ):
                    prod_info = prod_cfg.component_map.mapping[level_1_name][level_2_name][level_3_name]
                    prod_platorm = prod_info["platform"]
                    prod_path = prod_info["path"]

                    if stage_platform == "local":
                        for report_item_basename in os.listdir(stage_path):
                            girder_client.upload( os.path.join(stage_path,report_item_basename), prod_path, reuse_existing=False)
                        stage_cfg.component_map.mapping[level_1_name][level_2_name][level_3_name]["path"] = prod_path
                        stage_cfg.component_map.mapping[level_1_name][level_2_name][level_3_name]["platform"] = prod_platorm
                    else:
                        raise ValueError("Unexpected: non local path but benchmark is staged")

                else:
                    print(f"{level_1_name}-{level_2_name}-{level_3_name} not found in production... Adding it.")

                    tmp_location = os.path.join("./tmp",f"{level_1_name}_{level_3_name}_{level_2_name}")
                    shutil.move(stage_path,tmp_location)
                    uploaded_id = girder_client.upload( tmp_location, args.production_girder_id, return_id=True )

                    stage_cfg.component_map.mapping[level_1_name][level_2_name][level_3_name]["path"] = uploaded_id
                    stage_cfg.component_map.mapping[level_1_name][level_2_name][level_3_name]["platform"] = "girder"

    with open(args.stage_config,"w") as f:
        json.dump(stage_cfg.model_dump(),f)

    return 0