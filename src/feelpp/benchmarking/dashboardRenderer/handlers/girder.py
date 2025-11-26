from feelpp.benchmarking.dashboardRenderer.handlers.download import DownloadHandler
import girder_client
import os
from typing import Optional, List

class GirderHandler( DownloadHandler ):
    def __init__( self, download_base_dir:str ):
        """
        Handles connections, authentication, and file/folder transfers with a Girder server.
        It manages the connection details and provides methods to download and upload data to the remote platform.
        """
        super().__init__( download_base_dir = download_base_dir )
        self.base_url = "https://girder.math.unistra.fr/api/v1"
        self.initClient()

    def initClient( self ) -> None:
        """
        Initialize and authenticate the Girder client.

        The client attempts to authenticate using an API key provided via the environment variable `GIRDER_API_KEY`.

        Raises:
            ConnectionRefusedError: If the `GIRDER_API_KEY` environment variable is not set.
        """
        self.client = girder_client.GirderClient( apiUrl=self.base_url )
        if os.environ.get("GIRDER_API_KEY"):
            self.client.authenticate( apiKey=os.environ["GIRDER_API_KEY"] )
        else:
            raise ConnectionRefusedError("GIRDER_API_KEY is not set")

    def downloadFolder( self, folder_id:str, output_dir: Optional[str] = None ) -> List[str]:
        """
        Download a folder from Girder recursively.
        The remote folder content is downloaded into a local directory path relative to `self.download_base_dir`.

        Args:
            folder_id (str): The ID of the Girder folder to download.
            output_dir (Optional[str]): The optional subdirectory name within `self.download_base_dir` where content will be placed.
                                        If `None`, content is placed directly in `self.download_base_dir`.

        Returns:
            List[str]: The list of filenames downloaded inside the final output directory.
        """
        outdir = os.path.join( self.download_base_dir, output_dir ) if output_dir else self.download_base_dir
        self.client.downloadFolderRecursive( folder_id, outdir )

        if not os.path.exists( outdir ):
            print(f"Warning: folder with id {folder_id} was not correctly downloaded in {self.download_base_dir}/{output_dir}")
            return []

        return os.listdir( outdir )

    def downloadItem( self, item_id:str, output_dir:Optional[str]="" ) -> List[str]:
        """
        Download an item (which may contain multiple files) from Girder.
        The method ensures the target output directory exists before downloading.

        Args:
            item_id (str): The ID of the Girder item to download.
            output_dir (str): The path (relative to `self.download_base_dir`) to the output directory where the item's files will be placed.
        Returns:
            List[str]: The list of filenames downloaded inside the final output directory.
        """
        output_path = os.path.join( self.download_base_dir, output_dir )

        if not os.path.exists( output_path ):
            os.makedirs( output_path )

        self.client.downloadItem( itemId=item_id, dest=output_path )

        return os.listdir( output_path )



    def downloadFile( self, file_id:str, output_dir:Optional[str]="", name:Optional[str] = None ) -> None:
        """
        Download a single file from Girder. The output directory if it does not exist.

        Args:
            file_id (str): The ID of the file to download.
            output_dir (str): The path (relative to `self.download_base_dir`) to the output directory where the file will be placed.
            name (Optional[str]): The local filename to save the downloaded file as. If `None`, the file is saved directly into `output_path` (often using its original remote name).
        """
        output_path = os.path.join( self.download_base_dir, output_dir )

        if not os.path.exists( output_path ):
            os.makedirs( output_path )

        filepath = os.path.join( output_path, name ) if name else output_path

        self.client.downloadFile( fileId=file_id, path=filepath )

    def listChildren( self, parent_id:str, children_name:Optional[str] = None ) -> List:
        """
        List children (items or folders) within a Girder folder.
        If `children_name` is provided, it attempts to find a single item or folder with that name. Otherwise, it returns all children. It prioritizes listing items, then folders.

        Args:
            parent_id (str): The ID of the Girder folder to list children from.
            children_name (Optional[str]): The optional name of a specific child (item or folder) to find.
        Returns:
            List: A list of Girder dictionary representations of the children, or a single dictionary if `children_name` was provided.
        Raises:
            AssertionError: If `children_name` is provided but no child is found or if more than one child is found with that name.
        """
        items = list( self.client.listItem( folderId=parent_id, name=children_name ) )
        if len(items) == 0:
            items = list( self.client.listFolder( parentId=parent_id, name=children_name ) )

        if children_name:
            assert len(items) <=1, f"More than one file found with the same name {children_name}"
            assert len(items) >0, f"File not Found in Girder with the name {children_name}"
            return items[0]

        return items

    def upload( self, file_pattern :str, parent_id:str, leaf_folder_as_items:bool = True, reuse_existing:bool = True, return_id:bool = False ) -> Optional[str]:
        """
        Upload a local file or directory (matching a pattern) to an existing Girder folder.

        Args:
            file_pattern (str): The file pattern (e.g., a path to a file or a pattern like '*.txt') of the local files/directories to upload.
            parent_id (str): The ID of the target Girder folder to upload to. leaf_folder_as_items (bool): If True, leaf folders are uploaded as Girder items.
                                                                                            If False, their contents are uploaded as files. Defaults to True.
            reuse_existing (bool): If True, files with the same name will be replaced/reused. Defaults to True.
            return_id (bool): If True, the ID of the newly uploaded item is returned. Defaults to False.
        Returns:
            Optional[str]: The ID of the uploaded item if `return_id` is True, otherwise None.
        """
        self.client.upload(filePattern=file_pattern, parentId=parent_id, parentType="folder",leafFoldersAsItems=leaf_folder_as_items, reuseExisting=reuse_existing)

        if return_id:
            item = self.listChildren(parent_id,os.path.basename(file_pattern))
            return item["_id"]
