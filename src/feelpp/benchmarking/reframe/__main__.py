import os, json, subprocess, shutil
from feelpp.benchmarking.reframe.parser import Parser
from feelpp.benchmarking.reframe.config.configReader import ConfigReader
from feelpp.benchmarking.reframe.config.configSchemas import ConfigFile
from feelpp.benchmarking.reframe.config.configMachines import MachineConfig
from feelpp.benchmarking.reframe.reporting import WebsiteConfig
from feelpp.benchmarking.reframe.commandBuilder import CommandBuilder


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

        reframe_cmd = cmd_builder.buildCommand( app_reader.config.timeout)

        exit_code = subprocess.run(reframe_cmd, shell=True)

        #============ CREATING RESULT ITEM ================#
        with open(os.path.join(report_folder_path,"plots.json"),"w") as f:
            f.write(json.dumps([p.model_dump() for p in app_reader.config.plots]))


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

        #============== CLEANUP TEMPORARY DIRS ===============#
        if machine_reader.config.input_user_dir and app_reader.config.input_file_dependencies:
            temp_input_path = os.path.join(machine_reader.config.input_dataset_base_dir,"tmp")
            if not os.path.exists(temp_input_path):
                raise FileNotFoundError("input_user_dir is defined on machine config but did not create any temporary directory")
            shutil.rmtree(temp_input_path,ignore_errors = False)
        #=========================================================#

    if parser.args.website:
        subprocess.run(["render-benchmarks","--config-file", website_config.config_filepath])
        subprocess.run(["npm","run","antora"])
        subprocess.run(["npm","run","start"])

    # return exit_code.returncode
    return 0