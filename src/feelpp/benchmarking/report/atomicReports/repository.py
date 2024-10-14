from feelpp.benchmarking.report.atomicReports.atomicReport import AtomicReport
from feelpp.benchmarking.report.base.repository import Repository

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
        self.downloadAndInitAtomicReports(benchmarking_config_json, download_handler)

    def downloadAndInitAtomicReports(self,benchmarking_config_json, download_handler):
        """ Download the reports and initialize the atomic reports
        Args:
            benchmarking_config_json (dict): The benchmarking config JSON data
            download_handler (GirderHandler): The GirderHandler object to download the reports
        """
        for app_id, app_info in benchmarking_config_json.items():
            for machine_id, machine_info in app_info.items():
                outdir = f"{app_id}/{machine_id}"
                report_base_dirs = download_handler.downloadFolder(machine_info["girder_folder_id"], output_dir=outdir)
                for report_base_dir in report_base_dirs:
                    reframe_report_json = f"{download_handler.download_base_dir}/{outdir}/{report_base_dir}/reframe_report.json"
                    plots_config_json = f"{download_handler.download_base_dir}/{outdir}/{report_base_dir}/plots.json"
                    self.add(
                        AtomicReport(
                            application_id = app_id,
                            machine_id = machine_id,
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
            use_case = next(filter(lambda t: t.id == atomic_report.use_case_id and application in t.tree and machine in t.tree[application], use_cases))

            atomic_report.setIndexes(application, machine, use_case)

            machine.tree[application][use_case].append(atomic_report)
            application.tree[use_case][machine].append(atomic_report)
            use_case.tree[application][machine].append(atomic_report)