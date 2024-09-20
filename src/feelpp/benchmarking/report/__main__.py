import argparse,os
from feelpp.benchmarking.report.handlers import ConfigHandler, GirderHandler
from feelpp.benchmarking.report.machine import Machine
from feelpp.benchmarking.report.application import Application
from feelpp.benchmarking.report.repositories import AtomicReportRepository, MachineRepository, ApplicationRepository, TestCaseRepository

from feelpp.benchmarking.report.renderer import Renderer



def main_cli():
    parser = argparse.ArgumentParser(description="Render all benchmarking reports")
    parser.add_argument("--config_file", type=str, help="Path to the JSON config file", default="./src/feelpp/benchmarking/report/config.json")
    parser.add_argument("--json_output_path", type=str, help="Path to the output directory", default="reports")
    parser.add_argument("--modules_path", type=str, help="Path to the modules directory", default="./docs/modules/ROOT/pages")
    args = parser.parse_args()

    # Arguments treatment
    json_output_path = args.json_output_path[:-1] if args.json_output_path[-1] == "/" else args.json_output_path

    config_handler = ConfigHandler(args.config_file)
    girder_handler = GirderHandler(json_output_path)

    applications = ApplicationRepository(config_handler.applications)
    test_cases = TestCaseRepository(config_handler.applications)
    machines = MachineRepository(config_handler.machines)

    machines.link(applications, test_cases, config_handler.execution_mapping)
    applications.link(machines, test_cases, config_handler.execution_mapping)
    test_cases.link(applications, machines, config_handler.execution_mapping)

    index_renderer = Renderer("./src/feelpp/benchmarking/report/templates/index.adoc.j2")

    for machine in machines:
        machine.initModules(os.path.join(args.modules_path,"machines"), index_renderer,"supercomputers")


    # atomic_report = AtomicReportRepository(
    #     benchmarking_config_json = config_handler.execution_mapping,
    #     download_handler = girder_handler,
    # ).atomic_reports



if __name__ == "__main__":
    main_cli()