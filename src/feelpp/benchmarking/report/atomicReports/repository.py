from feelpp.benchmarking.report.atomicReports.atomicReport import AtomicReport
from feelpp.benchmarking.report.base.repository import Repository
import os
from datetime import datetime

class AtomicReportRepository(Repository):
    """ Repository for atomic reports """
    def __init__(self, benchmarking_config_json, download_handler):
        """ Constructor for the AtomicReportRepository class.
        Initializes the atomic reports from the benchmarking config JSON data
        after Downloading the reports using a download handler
        Args:
            benchmarking_config_json (dict): The benchmarking config JSON data
            download_handler (GirderHandler): The GirderHandler object to download the reports
        """
        self.data:list[AtomicReport] = []
        self.retrieveAndInitAtomicReports(benchmarking_config_json, download_handler)

    def retrieveAndInitAtomicReports(self,benchmarking_config_json, download_handler):
        """ Fetches the reports, downloading them depending on the specified platform and initialize the atomic reports
        Args:
            benchmarking_config_json (dict): The benchmarking config JSON data
            download_handler (GirderHandler): The GirderHandler object to download the reports
        """
        for app_id, app_info in benchmarking_config_json.items():
            for machine_id, machine_info in app_info.items():
                for use_case_id, use_case_info in machine_info.items():

                    if use_case_info["platform"] == "girder":
                        outdir = f"{app_id}/{machine_id}/{use_case_id}"
                        report_dirs = download_handler.downloadFolder(use_case_info["path"], output_dir=outdir)
                        report_dirs = [os.path.join(download_handler.download_base_dir,outdir,report_dir) for report_dir in report_dirs]
                    elif use_case_info["platform"] == "local":
                        report_dirs = os.listdir(use_case_info["path"])
                        report_dirs = [os.path.join(use_case_info["path"],report_dir) for report_dir in report_dirs]

                    for report_dir in report_dirs:
                        reframe_report_json = os.path.join(report_dir,"reframe_report.json")
                        plots_config_json = os.path.join(report_dir,"plots.json")
                        partials_dir = os.path.join(report_dir,"partials")
                        if not os.path.exists(partials_dir) or len(os.listdir(partials_dir)) == 0:
                            partials_dir = None
                        self.add(
                            AtomicReport(
                                application_id = app_id,
                                machine_id = machine_id,
                                use_case_id = use_case_id,
                                reframe_report_json = reframe_report_json,
                                plot_config_json=plots_config_json,
                                partials_dir = partials_dir
                            )
                        )

    def link(self, applications, machines, use_cases):
        """ Create the links between the atomic reports and the applications, machines and test cases
        An atomic report is identified by a single application, machine and test case
        the report is added to the respective tree of the application, machine and test case
        Args:
            applications (list[Application]): The list of applications
            machines (list[Machine]): The list of machines
            use_cases (list[UseCase]): The list of test cases
        """
        for atomic_report in self.data:
            application = applications.get(atomic_report.application_id)
            machine = machines.get(atomic_report.machine_id)
            use_case = use_cases.get(atomic_report.use_case_id)

            atomic_report.setIndexes(application, machine, use_case)

            machine.tree[application][use_case].append(atomic_report)
            application.tree[use_case][machine].append(atomic_report)
            use_case.tree[application][machine].append(atomic_report)


    def createOverview(self,base_dir, renderer, application, use_case, machine, reports):
        """Creates an overview for a single machine-app-use_case combination.
        The master dataframe of the Atomic report models are passed to the template, serialized.
        Args:
            base_dir (str): The base directory where the report will be created
            renderer (Renderer): The renderer to use
            application (Application) : The application the overview belongs to,
            use_case (UseCase) : The use case the overview belongs to,
            machine (Machine) : The machine the overview belongs to,
            reports (list[AtomicReport]). The atomic reports that are aggregated
        """

        renderer.render(
            os.path.join(base_dir,f"overview-{application.id}_{use_case.id}_{machine.id}.adoc"),
            dict(
                parent_catalogs = f"{application.id}-{use_case.id}-{machine.id},{machine.id}-{application.id}-{use_case.id},{use_case.id}-{application.id}-{machine.id}",
                reports_dfs = { report.date: report.model.master_df.to_dict(orient='dict') for report in reports },
                application = application,
                machine = machine,
                use_case = use_case
            )
        )

    def createOverviews(self, base_dir, renderer):
        """ Create the overviews for an app-machine-usecase combination, from aggregating atomic report data, by grouping reports ignoring the date
        Args:
            base_dir (str): The base directory where the report will be created
            renderer (Renderer): The renderer to use
        """

        if not os.path.exists(base_dir):
            os.mkdir(base_dir)

        grouped_atomic_reports = {}
        for atomic_report in self.data:
            overview_index = f"{atomic_report.application_id}_{atomic_report.use_case_id}_{atomic_report.machine_id}"

            if overview_index not in grouped_atomic_reports:
                grouped_atomic_reports[overview_index] = {
                    "reports":[atomic_report],
                    "application":atomic_report.application,
                    "use_case":atomic_report.use_case,
                    "machine":atomic_report.machine
                }
            else:
                grouped_atomic_reports[overview_index]["reports"].append(atomic_report)

        for ind,v in grouped_atomic_reports.items():
            self.createOverview(
                base_dir, renderer,
                application=v["application"],
                use_case=v["use_case"],
                machine=v["machine"],
                reports=v["reports"]
            )

    def createReports(self,base_dir, renderer):
        """ Create all atomic reports under a single directory
        Args:
            base_dir (str): The base directory where the report will be created
            renderer (Renderer): The renderer to use
        """
        if not os.path.exists(base_dir):
            os.mkdir(base_dir)

        for atomic_report in self.data:
            atomic_report.createReport(base_dir,renderer)

    def movePartials(self,base_dir):
        if not os.path.exists(base_dir):
            os.mkdir(base_dir)

        for atomic_report in self.data:
            atomic_report.movePartials(base_dir)


    def patchPlotConfigs(self,plot_configs, patch_reports_ids, save = False):
        """ Replaces the plot configuration with a new one.
        TODO: explain Cases (1 plot_config; many patches, ...)
        Args:
            plot_configs (list[str]): list of filepaths containing the new plot configuration.
            patch_reports_ids (list[str] ): list of report ids to filter patching, following the syntax machine-application-usecase-date. The date componenent accept the 'latest' keyword, and the application, use case and date component accept the 'all' keyword. If the list is empty, the latest report will be patched.
            save (bool): If true, it will replace the file contents of the old plots configuration
        """
        if plot_configs:
            if not patch_reports_ids: # 1 plot config, No reports to patch (select latest)
                if len(plot_configs)>1:
                    raise ValueError("When no patch reports are provided, plot configuration should be of length one")
                latest_report = max(self.data, key=lambda report: datetime.strptime(report.date, "%Y-%m-%dT%H:%M:%S%z"))
                latest_report.replacePlotsConfig(plot_configs[0], save)
            else:
                for i,patch_report in enumerate(patch_reports_ids):
                    #Filter reports based on ids
                    patch_machine, patch_application, patch_usecase, patch_date = patch_report
                    patch_machine_reports = list(filter(lambda x: x.machine_id == patch_machine, self.data))

                    if patch_application == "all":
                        patch_application_reports = patch_machine_reports
                    else:
                        patch_application_reports = list(filter(lambda x: x.application_id == patch_application, patch_machine_reports))

                    if patch_usecase == "all":
                        patch_usecase_reports = patch_application_reports
                    else:
                        patch_usecase_reports = list(filter(lambda x: x.use_case_id == patch_usecase, patch_application_reports))

                    if patch_date == "all":
                        reports_to_patch = patch_usecase_reports
                    elif patch_date == "latest":
                        reports_to_patch = [max(patch_usecase_reports, key=lambda report: datetime.strptime(report.date, "%Y-%m-%dT%H:%M:%S%z"))]
                    else:
                        reports_to_patch = list(filter(lambda x: datetime.strptime(x.date,"%Y-%m-%dT%H:%M:%S%z").strftime("%Y_%m_%dT%H_%M_%S") == patch_date, patch_usecase_reports))

                    for report_to_patch in reports_to_patch:
                        #1 plot config, many reports to patch
                        #Same number of plot config as reports to patch
                        plot_config = plot_configs[i] if len(patch_reports_ids) == len(plot_configs) else plot_configs[0] if len(plot_configs) == 1 else False
                        if not plot_config:
                            raise ValueError("Plots configuration must be either of length 1 or exactly the same lenght as patches")
                        report_to_patch.replacePlotsConfig(plot_config,save)
