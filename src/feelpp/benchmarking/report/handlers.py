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
        self.client.addItemUploadCallback(self.itemCallback)

        self.item_id = None

    def initClient(self):
        """ Initialize the Girder client """
        self.client = girder_client.GirderClient(apiUrl=self.base_url)
        self.client.authenticate(apiKey=os.environ["GIRDER_API_KEY"])

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

    def itemCallback(self,item,filepath):
        """ Callback to return the id of a created item"""
        self.item_id = item['_id']

    def uploadFileToFolder(self, input_filepath, parent_id):
        """ Upload a local file to an existing folder/item in Girder
        Args:
            input_filepath: The path of the file to upload
            parent_id (str): The ID of the Girder folder/item to upload to
            parent_type (str) : "folder" or "item". Defaults to "folder"
        """
        self.client.upload(filePattern=input_filepath, parentId=parent_id, parentType="folder")

    def uploadStringToItem(self, content, name, parent_id, parent_type):
        """ Writes a string into a temporary file,
            uploads the file to an existing folder/item in Girder,
            deletes the local file
        Args:
            content(str): The content to upload
            name: the file name to upload as
            parent_id (str): The ID of the Girder tem to upload to
        """
        self.client.uploadFile(parentId = parent_id,stream=io.StringIO(content),name=name,size=len(content),parentType=parent_type)


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
