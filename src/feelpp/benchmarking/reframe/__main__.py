import os, json, subprocess, shutil
from feelpp.benchmarking.reframe.parser import Parser
from feelpp.benchmarking.reframe.config.configReader import ConfigReader, FileHandler
from feelpp.benchmarking.reframe.schemas.benchmarkSchemas import ConfigFile
from feelpp.benchmarking.reframe.schemas.machines import MachineConfig
from feelpp.benchmarking.report.websiteConfigcreator import WebsiteConfigCreator
from feelpp.benchmarking.reframe.commandBuilder import CommandBuilder
from feelpp.benchmarking.dashboardRenderer.handlers.girder import GirderHandler

def main_cli():
    parser = Parser()
    parser.printArgs()


    os.environ["MACHINE_CONFIG_FILEPATH"] = parser.args.machine_config

    config_filepath = parser.args.benchmark_config
    os.environ["APP_CONFIG_FILEPATH"] = config_filepath


    configs = [{"":config_filepath}]
    if parser.args.machine_config:
        configs += [{"machine":parser.args.machine_config}]
    if parser.args.plots_config:
        configs += [{"json_report":parser.args.plots_config}]

    app_reader = ConfigReader(configs,ConfigFile,"app",dry_run=parser.args.dry_run)

    cmd_builder = CommandBuilder(app_reader.config.machine,parser)
    website_config = WebsiteConfigCreator(app_reader.config.machine.reports_base_dir)

    report_folder_path = cmd_builder.createReportFolder(app_reader.config.application_name,app_reader.config.use_case_name)

    #===============PULL IMAGES==================#
    if not parser.args.dry_run:
        for platform_name, platform_field in app_reader.config.platforms.items():
            if not platform_field.image or not platform_field.image.url or not app_reader.config.machine.containers[platform_name].executable:
                continue
            if platform_name == "apptainer":
                completed_pull = subprocess.run(f"{app_reader.config.machine.containers['apptainer'].executable} pull -F {platform_field.image.filepath} {platform_field.image.url}", shell=True)
                completed_pull.check_returncode()
            else:
                raise NotImplementedError(f"Image pulling is not yet supported for {platform_name}")
    #=============================================#

    #===== Download remote dependencies ============#
    if not parser.args.dry_run:
        if app_reader.config.remote_input_dependencies:
            if any(v.girder for v in app_reader.config.remote_input_dependencies.values()):
                girder_handler = GirderHandler(app_reader.config.machine.input_user_dir or app_reader.config.machine.input_dataset_base_dir  )
        for dependency_name,remote_dependency in app_reader.config.remote_input_dependencies.items():
            print(f"Donwloading remote file dependency : {dependency_name} ...")
            if remote_dependency.girder:
                if remote_dependency.girder.file:
                    girder_handler.downloadFile( remote_dependency.girder.file, os.path.dirname(remote_dependency.destination), name=os.path.basename(remote_dependency.destination) )
                elif remote_dependency.girder.folder:
                    girder_handler.downloadFolder(remote_dependency.girder.folder,remote_dependency.destination)
                elif remote_dependency.girder.item:
                    girder_handler.downloadItem(remote_dependency.girder.item,remote_dependency.destination)
                else:
                    raise NotImplementedError(f"Remote dependency resource type is not implemented for {dependency_name}")
            else:
                raise NotImplementedError(f"Platform {remote_dependency} is not implemented for {dependency_name}")
    #================================================#

    #============== UPDATE WEBSITE CONFIG FILE ==============#
    common_itempath = (parser.args.move_results or report_folder_path).split("/")
    common_itempath = "/".join(common_itempath[:-1 - (common_itempath[-1] == "")])

    website_config.updateExecutionMapping(
        app_reader.config.application_name, app_reader.config.machine.machine, app_reader.config.use_case_name,
        report_itempath = common_itempath
    )

    website_config.updateMachine(app_reader.config.machine.machine)
    website_config.updateUseCase(app_reader.config.use_case_name)
    website_config.updateApplication(app_reader.config.application_name)

    website_config.save()
    #======================================================#


    #============ CREATING RESULT ITEM ================#
    with open(os.path.join(report_folder_path,"report.json"),"w") as f:
        f.write(json.dumps(app_reader.config.json_report.model_dump()))

    #Copy use case description if existant
    FileHandler.copyResource(
        app_reader.config.additional_files.description_filepath,
        os.path.join(report_folder_path,"partials"),
        "description"
    )
    #===============================================#

    try:
        # ============== LAUNCH REFRAME =======================#
        reframe_cmd = cmd_builder.buildCommand( app_reader.config.timeout)
        exit_code = subprocess.run(reframe_cmd, shell=True)
        #======================================================#
    finally:
        if not os.path.exists(os.path.join(report_folder_path,"reframe_report.json")):
            if os.path.exists(os.path.join(report_folder_path,"report.json")):
                os.remove(os.path.join(report_folder_path,"report.json"))
            os.rmdir(report_folder_path)

    # ================== MOVE RESULTS (OPTION)============#
    if parser.args.move_results:
        if not os.path.exists(parser.args.move_results):
            os.makedirs(parser.args.move_results)
        os.rename(os.path.join(report_folder_path,"reframe_report.json"),os.path.join(parser.args.move_results,"reframe_report.json"))
        os.rename(os.path.join(report_folder_path,"report.json"),os.path.join(parser.args.move_results,"report.json"))
    #======================================================#

    if parser.args.website:
        subprocess.run(["feelpp-benchmarking-render","--config-file", website_config.config_filepath])
        subprocess.run(["npm","run","antora"])
        subprocess.run(["npm","run","start"])

    # return exit_code.returncode
    return 0