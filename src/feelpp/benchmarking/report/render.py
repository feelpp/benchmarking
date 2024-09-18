import json, glob, os, argparse
from jinja2 import Environment, FileSystemLoader
import girder_client

class Renderer:
    """ Class to render the JSON files to AsciiDoc files using Jinja2 templates"""

    def __init__(self, working_dir, template_path):
        """ Initialize the template for the renderer
        Args:
            working_dir (str): The working directory
            template_path (str, optional): The path to the Jinja2 template
        """
        env = Environment(loader=FileSystemLoader(working_dir), trim_blocks=True, lstrip_blocks=True)
        env.filters["convert_hostname"] = self.convert_hostname
        self.template = env.get_template(template_path)

    def render(self,input_json,output_filepath):
        """ Render the JSON file to an AsciiDoc file using a Jinja2 template
        Args:
            input_json (str): The path to the JSON file
            output_filepath (str): The path to the output AsciiDoc file
        """
        with open(input_json, 'r') as file:
            data = json.load(file)

        data['filename'] = input_json

        output = self.template.render(data)

        with open(output_filepath, 'w') as f:
            f.write(output)

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
            dict : dictionnary containing the downloaded file name hierarchy
        """
        self.client.downloadFolderRecursive(folder_id, output_path)

        filenames = {}
        for root, _, files in os.walk("reports"):
            if len(files) > 0:
                filenames[root] = files

        return filenames


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


def main_cli():
    """ CLI to download and render all benchmarking reports """

    GIRDER_ID_JSON_KEY = "girder_folder_id"
    WORKING_DIR = "./src/feelpp/benchmarking/report/"

    parser = argparse.ArgumentParser(description="Render all benchmarking reports")
    parser.add_argument("--config_file", type=str, help="Path to the JSON config file", default=WORKING_DIR+"config.json")
    parser.add_argument("--json_output_path", type=str, help="Path to the output directory", default="reports")
    parser.add_argument("--modules_path", type=str, help="Path to the modules directory", default="./docs/modules")
    args = parser.parse_args()

    # Arguments treatment
    json_output_path = args.json_output_path[:-1] if args.json_output_path[-1] == "/" else args.json_output_path

    config_handler = ConfigHandler(args.config_file)
    renderer = Renderer(working_dir = WORKING_DIR, template_path = "templates/benchmark.adoc.j2")
    girder_handler = GirderHandler()

    for app_id, machine_data in config_handler.benchmarks.items():
        assert app_id in config_handler.applications, f"Application {app_id} not found in the applications list"

        for machine_id, benchmarks_data in machine_data.items():
            assert machine_id in config_handler.machines, f"Machine {machine_id} not found in the machines list"

            if not GIRDER_ID_JSON_KEY in benchmarks_data: #TODO: Could use JSON schema to validate
                raise ValueError(f"Missing girder_folder_id for {app_id}/{machine_id}")

            folder_id = benchmarks_data[GIRDER_ID_JSON_KEY]

            #Download the app/machine folder from girder (multiple json files, indexed by date and input dataset)
            json_filenames = girder_handler.downloadFolder(folder_id, f"{json_output_path}/{app_id}/{machine_id}")

            #For each report, render the JSON file to AsciiDoc
            for json_folder, json_files in json_filenames.items():
                for json_filename in json_files:

                    if not json_filename.endswith(".json"):
                        continue

                    #Render the JSON file to AsciiDoc
                    adoc_output_path = f"{args.modules_path}/{machine_id}/{json_filename.replace('.json', '.adoc')}"
                    renderer.render(f"{json_folder}/{json_filename}", adoc_output_path)