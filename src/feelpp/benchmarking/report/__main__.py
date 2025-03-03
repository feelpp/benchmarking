import os, json, subprocess

from feelpp.benchmarking.report.config.handlers import ConfigHandler, GirderHandler
from feelpp.benchmarking.report.atomicReports.repository import AtomicReportRepository
from feelpp.benchmarking.report.machines.repository import MachineRepository
from feelpp.benchmarking.report.applications.repository import ApplicationRepository
from feelpp.benchmarking.report.useCases.repository import UseCaseRepository

from feelpp.benchmarking.report.renderer import RendererFactory
from feelpp.benchmarking.report.parser import ReportArgParser


def main_cli():
    parser = ReportArgParser()
    parser.printArgs()

    config_handler = ConfigHandler(parser.args.config_file)
    girder_handler = GirderHandler(parser.args.remote_download_dir)

    applications = ApplicationRepository(config_handler.applications)
    use_cases = UseCaseRepository(config_handler.use_cases)
    machines = MachineRepository(config_handler.machines)
    atomic_reports = AtomicReportRepository(config_handler.execution_mapping,girder_handler)

    machines.link(applications, use_cases, config_handler.execution_mapping)
    applications.link(machines, use_cases, config_handler.execution_mapping)
    use_cases.link(applications, machines, config_handler.execution_mapping)
    atomic_reports.link(applications, machines, use_cases)

    index_renderer = RendererFactory.create("index")
    overview_renderer = RendererFactory.create("atomic_overview")

    if parser.args.overview_config:
        with open(parser.args.overview_config,"r") as f:
            overview_config = json.load(f)

    if parser.args.plot_configs:
        atomic_reports.patchPlotConfigs(parser.args.plot_configs, parser.args.patch_reports, parser.args.save_patches)

    for repository in [applications,machines,use_cases]:
        repository.printHierarchy()
        repository.initModules(parser.args.modules_path, index_renderer, parent_id="catalog-index")

        if parser.args.overview_config:
            repository.initOverviewModels(overview_config)
            repository.createOverviews(parser.args.modules_path,overview_renderer)


    report_renderer = RendererFactory.create("benchmark")
    logs_renderer = RendererFactory.create("logs")

    atomic_reports.movePartials(os.path.join(parser.args.modules_path,"descriptions"))
    atomic_reports.createLogReports(os.path.join(parser.args.modules_path,"logs"),logs_renderer)
    atomic_reports.createReports(os.path.join(parser.args.modules_path,"reports"),report_renderer)

    if parser.args.website:
        subprocess.run(["npm","run","antora"])
        subprocess.run(["npm","run","start"])
