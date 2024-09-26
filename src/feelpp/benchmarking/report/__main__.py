import argparse,os
from feelpp.benchmarking.report.handlers import ConfigHandler, GirderHandler
from feelpp.benchmarking.report.components.repositories import AtomicReportRepository, MachineRepository, ApplicationRepository, TestCaseRepository

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
    use_cases = TestCaseRepository(config_handler.use_cases)
    machines = MachineRepository(config_handler.machines)

    atomic_reports = AtomicReportRepository(
        benchmarking_config_json = config_handler.execution_mapping,
        download_handler = girder_handler,
    )

    machines.link(applications, use_cases, config_handler.execution_mapping)
    applications.link(machines, use_cases, config_handler.execution_mapping)
    use_cases.link(applications, machines, config_handler.execution_mapping)

    atomic_reports.link(applications, machines, use_cases)


    machines.printHierarchy()
    print("-----------------")
    applications.printHierarchy()
    print("-----------------")
    use_cases.printHierarchy()


    index_renderer = Renderer("./src/feelpp/benchmarking/report/templates/index.adoc.j2")

    machines.initModules(os.path.join(args.modules_path,"machines"), index_renderer, parent_id="catalog-index")

    report_renderer = Renderer("./src/feelpp/benchmarking/report/templates/benchmark.adoc.j2")

    counter = {
        f"{mach.id}-{app.id}-{tc.id}" : 0
        for mach in machines
        for app,tcs in mach.tree.items()
        for tc in tcs
    }

    #TODO: At the moment just generate 5 reports per test case
    for atomic_report in atomic_reports:
        if counter[f"{atomic_report.machine_id}-{atomic_report.application_id}-{atomic_report.use_case_id}"] < 5:
            atomic_report.createReport(machines_base_dir,report_renderer)

        counter[f"{atomic_report.machine_id}-{atomic_report.application_id}-{atomic_report.use_case_id}"] += 1