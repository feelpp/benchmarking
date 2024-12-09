import os, json, io
import girder_client

class DownloadHandler:
    """ Base class for download handlers """
    def __init__(self,download_base_dir):
        """ Initialize the download handler
        Args:
            download_base_dir (str): The base directory for downloads
        """
        self.download_base_dir = download_base_dir

    def downloadFolder(self, folder_id, output_dir):
        """pure virtual function to download a folder"""
        pass

class GirderHandler(DownloadHandler):
    def __init__(self, download_base_dir):
        """ Initialize the Girder handler """
        super().__init__(download_base_dir = download_base_dir)
        self.base_url = "https://girder.math.unistra.fr/api/v1"
        self.initClient()

    def initClient(self):
        """ Initialize the Girder client """
        self.client = girder_client.GirderClient(apiUrl=self.base_url)
        if os.environ.get("GIRDER_API_KEY"):
            self.client.authenticate(apiKey=os.environ["GIRDER_API_KEY"])
        else:
            print("WARNING: Girder client was not initialized.")

    def downloadFolder(self, folder_id, output_dir):
        """ Download a folder from Girder recursively
        Args:
            folder_id (str): The ID of the folder to download
            output_path (str): The path to the output directory
        Returns:
            list: The list of downloaded files inside the output directory
        """
        self.client.downloadFolderRecursive(folder_id, f"{self.download_base_dir}/{output_dir}")

        if not os.path.exists(f"{self.download_base_dir}/{output_dir}"):
            print(f"Warning: folder with id {folder_id} was not correctly downloaded in {self.download_base_dir}/{output_dir}")
            return []

        return os.listdir(f"{self.download_base_dir}/{output_dir}")

    def downloadFile(self, file_id, output_dir="",name=None):
        """ Download a file from Girder. Creates the output dir if not exists
        Args:
            folder_id (str): The ID of the file to download
            output_path (str): The path to the output directory
        """
        output_path = os.path.join(self.download_base_dir,output_dir)

        if not os.path.exists(output_path):
            os.mkdir(output_path)

        filepath = os.path.join(output_path,name) if name else output_path

        self.client.downloadFile(fileId=file_id,path=filepath)

    def upload(self, file_pattern, parent_id,leaf_folder_as_items=True,reuse_existing=True):
        """ Upload a local file to an existing folder/item in Girder
        Args:
            file_pattern: The file pattern of the files to upload
            parent_id (str): The ID of the Girder folder/item to upload to
            parent_type (str) : "folder" or "item". Defaults to "folder"
            leaf_folder_as_items (bool): Whether to upload leaf folders as items or files
        """
        self.client.upload(filePattern=file_pattern, parentId=parent_id, parentType="folder",leafFoldersAsItems=leaf_folder_as_items, reuseExisting=reuse_existing)


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
        self.use_cases = config["use_cases"]
        self.execution_mapping = config["execution_mapping"]

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
