from feelpp.benchmarking.report.atomicReports.atomicReport import AtomicReport
from feelpp.benchmarking.report.base.repository import Repository
import os

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
                        self.add(
                            AtomicReport(
                                application_id = app_id,
                                machine_id = machine_id,
                                use_case_id = use_case_id,
                                reframe_report_json = reframe_report_json,
                                plot_config_json=plots_config_json
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