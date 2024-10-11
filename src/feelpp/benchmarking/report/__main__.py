import argparse,os
from feelpp.benchmarking.report.handlers import ConfigHandler, GirderHandler
from feelpp.benchmarking.report.components.repositories import AtomicReportRepository, MachineRepository, ApplicationRepository, UseCaseRepository

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
    use_cases = UseCaseRepository(config_handler.use_cases)
    machines = MachineRepository(config_handler.machines)
    atomic_reports = AtomicReportRepository(config_handler.execution_mapping,girder_handler)

    machines.link(applications, use_cases, config_handler.execution_mapping)
    applications.link(machines, use_cases, config_handler.execution_mapping)
    use_cases.link(applications, machines, config_handler.execution_mapping)
    atomic_reports.link(applications, machines, use_cases)

    index_renderer = Renderer("./src/feelpp/benchmarking/report/templates/index.adoc.j2")
    machine_report_renderer = Renderer("./src/feelpp/benchmarking/report/templates/machine.adoc.j2")
    report_renderer = Renderer("./src/feelpp/benchmarking/report/templates/benchmark.adoc.j2")

    applications_base_dir = os.path.join(args.modules_path,"applications")
    applications.initModules(applications_base_dir, index_renderer, parent_id="catalog-index")

    for machine in machines:
        machine.createOverview(applications_base_dir,machine_report_renderer)

    for atomic_report in atomic_reports:
        atomic_report.createReport(applications_base_dir,report_renderer)