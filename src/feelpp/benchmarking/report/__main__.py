import argparse, os

from feelpp.benchmarking.report.config.handlers import ConfigHandler, GirderHandler
from feelpp.benchmarking.report.atomicReports.repository import AtomicReportRepository
from feelpp.benchmarking.report.machines.repository import MachineRepository
from feelpp.benchmarking.report.applications.repository import ApplicationRepository
from feelpp.benchmarking.report.useCases.repository import UseCaseRepository

from feelpp.benchmarking.report.renderer import RendererFactory



def main_cli():
    parser = argparse.ArgumentParser(description="Render all benchmarking reports")
    parser.add_argument("--config_file", type=str, help="Path to the JSON config file", default="./src/feelpp/benchmarking/report/config/config.json")
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

    index_renderer = RendererFactory.create("index")

    print("----- APPLICATIONS VIEW -------")
    applications.printHierarchy()
    applications.initModules(args.modules_path, index_renderer, parent_id="catalog-index")
    print("-------------------------------")

    print("----- MACHINES VIEW -------")
    machines.printHierarchy()
    machines.initModules(args.modules_path, index_renderer, parent_id="catalog-index")
    print("-------------------------------")

    print("----- USE CASES VIEW -------")
    use_cases.printHierarchy()
    use_cases.initModules(args.modules_path, index_renderer, parent_id="catalog-index")
    print("-------------------------------")


    overview_renderer = RendererFactory.create("atomic_overview")
    atomic_reports.createOverviews(os.path.join(args.modules_path,"overviews"),overview_renderer)


    report_renderer = RendererFactory.create("benchmark")
    atomic_reports.createReports(os.path.join(args.modules_path,"reports"),report_renderer)