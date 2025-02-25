import os, json, subprocess, shutil
from feelpp.benchmarking.reframe.parser import Parser
from feelpp.benchmarking.reframe.config.configReader import ConfigReader, FileHandler
from feelpp.benchmarking.reframe.config.configSchemas import ConfigFile
from feelpp.benchmarking.reframe.config.configMachines import MachineConfig
from feelpp.benchmarking.reframe.reporting import WebsiteConfig
from feelpp.benchmarking.reframe.commandBuilder import CommandBuilder
from feelpp.benchmarking.report.config.handlers import GirderHandler

def main_cli():
    parser = Parser()
    parser.printArgs()

    machine_reader = ConfigReader(parser.args.machine_config,MachineConfig,"machine",dry_run=parser.args.dry_run)

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

    os.environ["MACHINE_CONFIG_FILEPATH"] = parser.args.machine_config

    website_config = WebsiteConfig(machine_reader.config.reports_base_dir)

    for config_filepath in parser.args.benchmark_config:
        os.environ["APP_CONFIG_FILEPATH"] = config_filepath


        configs = [config_filepath]
        if parser.args.plots_config:
            configs += [parser.args.plots_config]
        app_reader = ConfigReader(configs,ConfigFile,"app",dry_run=parser.args.dry_run,additional_readers=[machine_reader])

        executable_name = os.path.basename(app_reader.config.executable).split(".")[0]
        report_folder_path = cmd_builder.createReportFolder(executable_name,app_reader.config.use_case_name)

        #===============PULL IMAGES==================#
        if not parser.args.dry_run:
            for platform_name, platform_field in app_reader.config.platforms.items():
                if not platform_field.image or not platform_field.image.remote or not machine_reader.config.containers[platform_name].executable:
                    continue
                if platform_name == "apptainer":
                    #TODO: Check exit code
                    subprocess.run(f"{machine_reader.config.containers['apptainer'].executable} pull -F {platform_field.image.name} {platform_field.image.remote}", shell=True)
                else:
                    raise NotImplementedError(f"Image pulling is not yet supported for {platform_name}")
        #=============================================#

        #===== Download remote dependencies ============#
        if app_reader.config.remote_input_dependencies:
            if any(v.platform for v in app_reader.config.remote_input_dependencies.values()):
                girder_handler = GirderHandler(machine_reader.config.input_dataset_base_dir)
        for dependency_name,remote_dependency in app_reader.config.remote_input_dependencies.items():
            print(f"Donwloading remote file dependency : {dependency_name} ...")
            if remote_dependency.platform == "girder":
                if remote_dependency.type == "file":
                    girder_handler.downloadFile(
                        remote_dependency.remote_location,
                        os.path.dirname(remote_dependency.destination),
                        name=os.path.basename(remote_dependency.destination)
                    )
                elif remote_dependency.type == "folder":
                    girder_handler.downloadFolder(remote_dependency.remote_location,remote_dependency.destination)
                elif remote_dependency.type == "item":
                    girder_handler.downloadItem(remote_dependency.remote_location,remote_dependency.destination)
                else:
                    raise NotImplementedError(f"Type {remote_dependency.type} is not implemented for {dependency_name}")
            else:
                raise NotImplementedError(f"Platform {remote_dependency.platform} is not implemented for {dependency_name}")
        #================================================#

        reframe_cmd = cmd_builder.buildCommand( app_reader.config.timeout)

        exit_code = subprocess.run(reframe_cmd, shell=True)

        #============ CREATING RESULT ITEM ================#
        with open(os.path.join(report_folder_path,"plots.json"),"w") as f:
            f.write(json.dumps([p.model_dump() for p in app_reader.config.plots]))

        #Copy use case description if existant
        FileHandler.copyFile(
            os.path.join(report_folder_path,"partials"),
            "description",
            app_reader.config.additional_files.description_filepath
        )

        if parser.args.move_results:
            if not os.path.exists(parser.args.move_results):
                os.makedirs(parser.args.move_results)
            os.rename(os.path.join(report_folder_path,"reframe_report.json"),os.path.join(parser.args.move_results,"reframe_report.json"))
            os.rename(os.path.join(report_folder_path,"plots.json"),os.path.join(parser.args.move_results,"plots.json"))
        #======================================================#

        #============== UPDATE WEBSITE CONFIG FILE ==============#
        common_itempath = (parser.args.move_results or report_folder_path).split("/")
        common_itempath = "/".join(common_itempath[:-1 - (common_itempath[-1] == "")])

        website_config.updateExecutionMapping(
            executable_name, machine_reader.config.machine, app_reader.config.use_case_name,
            report_itempath = common_itempath
        )

        website_config.updateMachine(machine_reader.config.machine)
        website_config.updateUseCase(app_reader.config.use_case_name)
        website_config.updateApplication(executable_name)

        website_config.save()
        #======================================================#

    if parser.args.website:
        subprocess.run(["render-benchmarks","--config-file", website_config.config_filepath])
        subprocess.run(["npm","run","antora"])
        subprocess.run(["npm","run","start"])

    # return exit_code.returncode
    return 0