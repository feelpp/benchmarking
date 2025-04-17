from feelpp.benchmarking.dashboardRenderer.handlers.download import DownloadHandler
import girder_client
import os

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
            raise ConnectionRefusedError("GIRDER_API_KEY is not set")

    def downloadFolder(self, folder_id, output_dir=None):
        """ Download a folder from Girder recursively
        Args:
            folder_id (str): The ID of the folder to download
            output_path (str): The path to the output directory
        Returns:
            list: The list of downloaded files inside the output directory
        """
        outdir = os.path.join(self.download_base_dir,output_dir) if output_dir else self.download_base_dir
        self.client.downloadFolderRecursive(folder_id, outdir)

        if not os.path.exists(outdir):
            print(f"Warning: folder with id {folder_id} was not correctly downloaded in {self.download_base_dir}/{output_dir}")
            return []

        return os.listdir(outdir)

    def downloadItem(self, item_id, output_dir=""):
        """ Download an item from Girder. Creates the output dir if not exists
        Args:
            item_id (str): The ID of the item to download
            output_dir (str): The path to the output directory
        """
        output_path = os.path.join(self.download_base_dir,output_dir)

        if not os.path.exists(output_path):
            os.makedirs(output_path)

        self.client.downloadItem(itemId=item_id,dest=output_path)

        return os.listdir(output_path)



    def downloadFile(self, file_id, output_dir="",name=None):
        """ Download a file from Girder. Creates the output dir if not exists
        Args:
            file_id (str): The ID of the file to download
            output_path (str): The path to the output directory
        """
        output_path = os.path.join(self.download_base_dir,output_dir)

        if not os.path.exists(output_path):
            os.makedirs(output_path)

        filepath = os.path.join(output_path,name) if name else output_path

        self.client.downloadFile(fileId=file_id,path=filepath)

    def listChildren(self,parent_id, children_name = None):
        items = list(self.client.listItem(folderId=parent_id, name=children_name))
        if len(items) == 0:
            items = list(self.client.listFolder(parentId=parent_id, name=children_name))

        if children_name:
            assert len(items) <=1, f"More than one file found with the same name {children_name}"
            assert len(items) >0, f"File not Found in Girder with the name {children_name}"
            return items[0]

        return items

    def upload(self, file_pattern, parent_id,leaf_folder_as_items=True,reuse_existing=True, return_id=False):
        """ Upload a local file to an existing folder/item in Girder
        Args:
            file_pattern: The file pattern of the files to upload
            parent_id (str): The ID of the Girder folder/item to upload to
            parent_type (str) : "folder" or "item". Defaults to "folder"
            leaf_folder_as_items (bool): Whether to upload leaf folders as items or files
        """
        self.client.upload(filePattern=file_pattern, parentId=parent_id, parentType="folder",leafFoldersAsItems=leaf_folder_as_items, reuseExisting=reuse_existing)

        if return_id:
            item = self.listChildren(parent_id,os.path.basename(file_pattern))
            return item["_id"]
