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

    if parser.args.machine_config:
        machine_reader = ConfigReader(parser.args.machine_config,MachineConfig,"machine",dry_run=parser.args.dry_run)
    else:
        machine_reader = ConfigReader(None,MachineConfig,"machine",dry_run=parser.args.dry_run)
        machine_reader.config = MachineConfig(machine="default")


    #Sets the cachedir and tmpdir directories for containers
    for platform, dirs in machine_reader.config.containers.items():
        if platform=="apptainer":
            if dirs.cachedir:
                os.environ["APPTAINER_CACHEDIR"] = dirs.cachedir
            if dirs.tmpdir:
                os.environ["APPTAINER_TMPDIR"] = dirs.cachedir
        elif platform=="docker":
            raise NotImplementedError("Docker container directories configuration is not implemented")

    cmd_builder = CommandBuilder(machine_reader.config,parser)

    if parser.args.machine_config:
        os.environ["MACHINE_CONFIG_FILEPATH"] = parser.args.machine_config

    website_config = WebsiteConfigCreator(machine_reader.config.reports_base_dir)

    for config_filepath in parser.args.benchmark_config:
        os.environ["APP_CONFIG_FILEPATH"] = config_filepath


        configs = [{"":config_filepath}]
        if parser.args.plots_config:
            configs += [{"json_report":parser.args.plots_config}]
        app_reader = ConfigReader(configs,ConfigFile,"app",dry_run=parser.args.dry_run,additional_readers=[machine_reader])

        application_name = app_reader.config.application_name
        if parser.args.dry_run:
            report_folder_path = None
        else:
            report_folder_path = cmd_builder.createReportFolder(application_name,app_reader.config.use_case_name)

        #===============PULL IMAGES==================#
        if not parser.args.dry_run:
            for platform_name, platform_field in app_reader.config.platforms.items():
                if not platform_field.image or not platform_field.image.url or not machine_reader.config.containers[platform_name].executable:
                    continue
                if platform_name == "apptainer":
                    completed_pull = subprocess.run(f"{machine_reader.config.containers['apptainer'].executable} pull -F {platform_field.image.filepath} {platform_field.image.url}", shell=True)
                    completed_pull.check_returncode()
                else:
                    raise NotImplementedError(f"Image pulling is not yet supported for {platform_name}")
        #=============================================#

        #===== Download remote dependencies ============#
        if not parser.args.dry_run:
            if app_reader.config.remote_input_dependencies:
                if any(v.girder for v in app_reader.config.remote_input_dependencies.values()):
                    girder_handler = GirderHandler(machine_reader.config.input_user_dir or machine_reader.config.input_dataset_base_dir  )
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
        if not parser.args.dry_run:
            common_itempath = (parser.args.move_results or report_folder_path).split("/")
            common_itempath = "/".join(common_itempath[:-1 - (common_itempath[-1] == "")])

            website_config.updateExecutionMapping(
                application_name, machine_reader.config.machine, app_reader.config.use_case_name,
                report_itempath = common_itempath
            )

            website_config.updateMachine(machine_reader.config.machine)
            website_config.updateUseCase(app_reader.config.use_case_name)
            website_config.updateApplication(application_name)

            website_config.save()
        #======================================================#


        #============ CREATING RESULT ITEM ================#
        if not parser.args.dry_run:
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
            reframe_cmd = cmd_builder.buildCommand( app_reader.config.timeout )
            exit_code = subprocess.run(reframe_cmd, shell=True)
            #======================================================#
        finally:
            if report_folder_path and not os.path.exists(os.path.join(report_folder_path,"reframe_report.json")):
                if os.path.exists(os.path.join(report_folder_path,"report.json")):
                    os.remove(os.path.join(report_folder_path,"report.json"))
                os.rmdir(report_folder_path)


        #================= MERGE RESTORED SESSION REPORTS =============#
        if "--restore-session" in parser.args.reframe_args:
            reframe_args = parser.args.reframe_args.split(" ")
            restore_session_index = reframe_args.index("--restore-session")
            restore_session_path = reframe_args[restore_session_index + 1]
            if not os.path.exists(restore_session_path) or not os.path.isfile(restore_session_path):
                raise FileNotFoundError(f"Restore session path {restore_session_path} does not exist")
            with open(restore_session_path,"r") as f:
                restored_report = json.load(f)
            with open(os.path.join(report_folder_path,"reframe_report.json"),"r") as f:
                current_report = json.load(f)
            restored_report["runs"].extend(current_report["runs"])
            restored_report["session_info"]["num_cases"] = max([run["num_cases"] for run in restored_report["runs"]])
            restored_report["session_info"]["num_failures"] = min([run["num_failures"] for run in restored_report["runs"]])

            with open(restore_session_path,"w") as f:
                json.dump(restored_report,f,indent=4)

            #Update logs and partials
            new_logs_dir = os.path.join(report_folder_path,"logs")
            restored_logs_dir = os.path.join(os.path.dirname(restore_session_path),"logs")
            #Copy new logs into restored, overwrite if existant
            if os.path.exists(restored_logs_dir):
                if os.path.exists(new_logs_dir):
                    for log_file in os.listdir(new_logs_dir):
                        shutil.copy(os.path.join(new_logs_dir,log_file),restored_logs_dir)
            else:
                if os.path.exists(new_logs_dir):
                    shutil.copytree(new_logs_dir,restored_logs_dir)

            new_partials_dir = os.path.join(report_folder_path,"partials")
            restored_partials_dir = os.path.join(os.path.dirname(restore_session_path),"partials")
            #Copy new partials into restored, overwrite if existant
            if os.path.exists(restored_partials_dir):
                if os.path.exists(new_partials_dir):
                    for partial_file in os.listdir(new_partials_dir):
                        shutil.copy(os.path.join(new_partials_dir,partial_file),restored_partials_dir)
            else:
                if os.path.exists(new_partials_dir):
                    shutil.copytree(new_partials_dir,restored_partials_dir)

            #Remove current report folder
            if os.path.exists(report_folder_path):
                shutil.rmtree(report_folder_path)
        #======================================================#



        # ================== MOVE RESULTS (OPTION)============#
        if parser.args.move_results:
            if not os.path.exists(parser.args.move_results):
                os.makedirs(parser.args.move_results)
            if report_folder_path:
                os.rename(os.path.join(report_folder_path,"reframe_report.json"),os.path.join(parser.args.move_results,"reframe_report.json"))
                os.rename(os.path.join(report_folder_path,"report.json"),os.path.join(parser.args.move_results,"report.json"))
        #======================================================#

    if parser.args.website:
        subprocess.run(["feelpp-benchmarking-render","--config-file", website_config.config_filepath])
        subprocess.run(["npm","run","antora"])
        subprocess.run(["npm","run","start"])

    # return exit_code.returncode
    return 0
