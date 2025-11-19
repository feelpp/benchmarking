
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

class SingletonMeta(type):
    """ A metaclass for creating singletons """
    _instances = {}

    def __call__( cls, *args, **kwargs ):
        if cls not in cls._instances:
            instance = super().__call__( *args, **kwargs )
            cls._instances[cls] = instance
        return cls._instances[cls]