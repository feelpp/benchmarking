import json, glob, os, argparse
from jinja2 import Environment, FileSystemLoader
import girder_client

class Renderer:
    """ Base Class to render the JSON files to AsciiDoc files using Jinja2 templates"""

    def __init__(self, working_dir, template_path, filters = {}):
        """ Initialize the template for the renderer
        Args:
            working_dir (str): The working directory
            template_path (str, optional): The path to the Jinja2 template
            filters (dict, optional): The filters to add to the Jinja2 environment
        """
        env = Environment(loader=FileSystemLoader(working_dir), trim_blocks=True, lstrip_blocks=True)
        for name, filter in filters.items():
            env.filters[name] = filter
        self.template = env.get_template(template_path)

    def render(self, output_filepath, data):
        """ Render the JSON file to an AsciiDoc file using a Jinja2 template and the given data"""
        output = self.template.render(data)

        with open(output_filepath, 'w') as f:
            f.write(output)


class IndexRenderer(Renderer):
    """ Class to render the index files for the modules """
    def __init__(self, working_dir, template_path):
        """ Initialize the index renderer
        Args:
            working_dir (str): The working directory
            template_path (str): The path to the Jinja2 template, relative to the working directory
        """
        super().__init__(working_dir, template_path)

    def render(self, output_folder_path, data):
        """ Render the index file for the module
        Args:
            output_folder_path (str): The path to the output directory
            data (dict): The data to render
        """
        output_filepath = f"{output_folder_path}/index.adoc"
        super().render(output_filepath, data)



class ReportRenderer(Renderer):
    """ Class to render the JSON files to AsciiDoc files for the benchmarking reports """
    def __init__(self, working_dir, template_path):
        """ Initialize the report renderer
        Args:
            working_dir (str): The working directory
            template_path (str): The path to the Jinja2 template, relative to the working directory
        """
        filters = {"convert_hostname": self.convert_hostname}
        super().__init__(working_dir, template_path, filters)

    def parseData(self, input_json):
        """ Parse the JSON file to add or modify some fields
        Args:
            input_json (str): The path to the JSON file
        Returns:
            dict: The parsed JSON file
        """
        with open(input_json, 'r') as file:
            data = json.load(file)

        data['filepath'] = input_json
        return data

    def render(self,input_json,output_folderpath, machine_id, application_id, case_tags):
        """ Render the JSON file to an AsciiDoc file using a Jinja2 template
        Args:
            input_json (str): The path to the JSON file
            output_folderpath (str): The path to the output AsciiDoc file
            case_tags (list): The list of all possible test cases for an app, to be found in the JSON file
        """
        data = self.parseData(input_json)

        tags = data["runs"][0]["testcases"][0]["tags"] #TODO: Make sure that all testcases and runs have same tags.
        current_test_case = "default"
        for case_tag in case_tags:
            if case_tag in tags:
                current_test_case = case_tag
                break

        data["machine_id"] = machine_id
        data['application_id'] = application_id
        data['test_case_id'] = current_test_case

        output_filepath = f"{output_folderpath}/{current_test_case}/{input_json.split("/")[-1].replace('.json', '.adoc')}"
        super().render(output_filepath, data)

    @staticmethod
    def convert_hostname(hostname):
        """ Parse the hostname to a more readable format
        Args:
            hostname (str): The hostname to parse
        Returns:
            str: The parsed hostname
        """
        if hostname.startswith("mel"):
            return "meluxina"
        if "karolina" in hostname:
            return "karolina"
        if "discoverer" in hostname:
            return "discoverer"
        if "gaya" in hostname:
            return "gaya"
        if "uan" in hostname:
            return "lumi"
        return hostname

class GirderHandler:
    def __init__(self):
        """ Initialize the Girder handler """
        self.base_url = "https://girder.math.unistra.fr/api/v1"
        self.initClient()

    def initClient(self):
        """ Initialize the Girder client """
        self.client = girder_client.GirderClient(apiUrl=self.base_url)
        self.client.authenticate(apiKey=os.environ["GIRDER_API_KEY"])

    def downloadFolder(self, folder_id, output_path):
        """ Download a folder from Girder recursively
        Args:
            folder_id (str): The ID of the folder to download
            output_path (str): The path to the output directory
        Returns:
            list: The list of downloaded files inside the output directory
        """
        self.client.downloadFolderRecursive(folder_id, output_path)

        return os.listdir(output_path)



class ConfigHandler:
    def __init__(self, config_filepath):
        """ Initialize the configuration handler
        Args:
            config_filepath (str): The path to the configuration file
        """

        #Checks
        self.checkFileExists(filepath=config_filepath)
        self.checkFileExtension(filepath=config_filepath, extension="json")

        with open(config_filepath, 'r') as file:
            config = json.load(file)

        self.machines = config["machines"]
        self.applications = config["applications"]
        self.benchmarks = config["benchmarks"]

    def checkFileExists(self, filepath):
        """ Check if a file exists
        Args:
            filepath (str): The path to the file
        Raises:
            FileNotFoundError: If the file does not exist
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File {filepath} not found")

    def checkFileExtension(self, filepath, extension):
        """ Check if the file has a given extension file
        Args:
            filepath (str): The path to the file
            extension (str): The extension to check (without the dot)
        Raises:
            ValueError: If the file does not have the given extension
        """
        if not filepath.split(".")[-1] == extension:
            raise ValueError("The config file must be a JSON file")

    def initializeModules(self, index_renderer:IndexRenderer, base_dir = "docs/modules/ROOT/pages"):
        """ Create directories and respective index files for all modules inside the config file
        It does not create the directories for machines, an error will be raised if a machine is not found
        Args:
            index_renderer (IndexRenderer): The renderer to render the index files
            base_dir (str, optional): The base directory to create the directories. Defaults to "docs/modules/ROOT/pages"
        """

        for app_id, machines in self.benchmarks.items():

            for machine_id, benchmarks in machines.items():
                machine_path = f"{base_dir}/machines/{machine_id}"
                assert os.path.exists(machine_path), f"Machine {machine_id} not found in the modules directory. Either remove it from the config file, or create the directory"

                app_path = f"{machine_path}/pages/{app_id}/pages"
                os.makedirs(app_path, exist_ok=True)

                index_renderer.render(
                    output_folder_path = app_path,
                    data = {
                        "title": self.applications[app_id]["display_name"],
                        "layout":"toolboxes",
                        "tags": f"catalog, toolbox, {machine_id}-{app_id}",
                        "parent_catalogs": f"{machine_id}",
                        "illustration": f"ROOT:{self.applications[app_id]['thumbnail']}"
                    }
                )

                for test_case in benchmarks["test_cases"]:
                    test_case_path = f"{app_path}/{test_case}"

                    if not os.path.exists(test_case_path):
                        os.mkdir(test_case_path)

                    test_case_info = self.applications[app_id]["test_cases"][test_case]
                    index_renderer.render(
                        output_folder_path = test_case_path,
                        data = {
                            "title": test_case_info["name"],
                            "description": test_case_info["description"],
                            "layout": "toolboxes",
                            "tags": f"catalog, toolbox, {machine_id}-{app_id}-{test_case}",
                            "parent_catalogs": f"{machine_id}-{app_id}"
                        }
                    )

def main_cli():
    """ CLI to download and render all benchmarking reports """

    GIRDER_ID_JSON_KEY = "girder_folder_id"
    WORKING_DIR = "./src/feelpp/benchmarking/report/"
    LATEST_REPORTS_TO_KEEP = 5 #TODO: Use another logic

    parser = argparse.ArgumentParser(description="Render all benchmarking reports")
    parser.add_argument("--config_file", type=str, help="Path to the JSON config file", default=WORKING_DIR+"config.json")
    parser.add_argument("--json_output_path", type=str, help="Path to the output directory", default="reports")
    parser.add_argument("--modules_path", type=str, help="Path to the modules directory", default="./docs/modules/ROOT/pages")
    args = parser.parse_args()

    # Arguments treatment
    json_output_path = args.json_output_path[:-1] if args.json_output_path[-1] == "/" else args.json_output_path

    config_handler = ConfigHandler(args.config_file)
    renderer = ReportRenderer(working_dir = WORKING_DIR, template_path = "templates/benchmark.adoc.j2")
    girder_handler = GirderHandler()


    index_renderer = IndexRenderer(working_dir = WORKING_DIR, template_path = "templates/index.adoc.j2")
    config_handler.initializeModules(index_renderer)

    for app_id, machine_data in config_handler.benchmarks.items():
        assert app_id in config_handler.applications, f"Application {app_id} not found in the applications list"

        for machine_id, benchmarks_data in machine_data.items():
            assert machine_id in config_handler.machines, f"Machine {machine_id} not found in the machines list"

            if not GIRDER_ID_JSON_KEY in benchmarks_data: #TODO: Could use JSON schema to validate
                raise ValueError(f"Missing girder_folder_id for {app_id}/{machine_id}")

            folder_id = benchmarks_data[GIRDER_ID_JSON_KEY]

            #Download the app/machine folder from girder (multiple json files, indexed by date and input dataset)
            json_filenames = girder_handler.downloadFolder(folder_id, f"{json_output_path}/{app_id}/{machine_id}")

            json_filenames.sort() #TODO: CORRECT SORTING BY DATE
            json_filenames = json_filenames[:LATEST_REPORTS_TO_KEEP]

            test_cases = benchmarks_data["test_cases"]

            #For each report, render the JSON file to AsciiDoc
            for json_filename in json_filenames:
                #Render the JSON file to AsciiDoc
                output_folder_path = f"{args.modules_path}/machines/{machine_id}/pages/{app_id}/pages"

                renderer.render(
                    f"{json_output_path}/{app_id}/{machine_id}/{json_filename}",
                    output_folder_path,
                    machine_id=machine_id,
                    application_id=app_id,
                    case_tags = test_cases
                )