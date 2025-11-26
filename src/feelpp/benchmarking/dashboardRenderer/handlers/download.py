
class DownloadHandler:
    """ Base class for download handlers """
    def __init__( self, download_base_dir:str ):
        """ Initialize the download handler
        Args:
            download_base_dir (str): The base directory for downloads
        """
        self.download_base_dir = download_base_dir

    def downloadFolder( self, folder_id, output_dir ):
        """Pure virtual function to download a folder"""
        raise NotImplementedError("Pure virtual function to download a folder")