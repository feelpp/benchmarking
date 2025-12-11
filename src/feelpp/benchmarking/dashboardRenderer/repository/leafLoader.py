from feelpp.benchmarking.dashboardRenderer.repository.base import Repository
from feelpp.benchmarking.dashboardRenderer.component.leaf import LeafComponent
from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import LeafMetadata
from feelpp.benchmarking.dashboardRenderer.views.base import ViewFactory
from feelpp.benchmarking.dashboardRenderer.handlers.girder import GirderHandler
from feelpp.benchmarking.dashboardRenderer.schemas.dashboardSchema import TemplateInfo
import os, tempfile, warnings
from typing import Dict, List

class LeafLoader:
    """
    Abstract base class defining the interface for loading leaf components.

    Derived classes must implement the `load` method to define the specific
    mechanism for retrieving components (e.g., from local disk, a remote server).
    """
    def __init__( self, location:str, template_info:TemplateInfo ) -> None:
        """
        Args:
            location (str): The source location of the leaf components (e.g., a file path or a Girder path).
            template_info (Dict[str, Any]): Information about the view template to be used when creating the LeafComponent's view.
        """
        self.location = location
        self.template_info = template_info

    def load( self, repository:Repository, parent_ids:List[str] ) -> None:
        """
        Load leaf components into the repository.

        This is a pure virtual method that must be implemented by concrete subclasses.

        Args:
            repository (Repository): The repository instance to load components into.
            parent_ids (List[str]): List of parent IDs for the components, establishing a hierarchy.

        Raises:
            NotImplementedError: If the method is not implemented in a derived class.
        """
        raise NotImplementedError("Pure virtual method, must be implemented in derived classes.")


class LocalLeafLoader(LeafLoader):
    """
    Concrete loader for leaf components residing on the local filesystem.
    It assumes that the components are organized in subdirectories within the specified location.
    """
    def __init__(self, location:str, template_info: TemplateInfo) -> None:
        """
        Args:
            location (Optional[str]): The local directory containing leaf components.
            template_info (Dict[str, Any]): Information about the view template.
        Warns:
            UserWarning: If the specified location does not exist, but only if location is provided.
        """
        super().__init__( location, template_info )

        if not location:
            return
        if not os.path.exists( location ):
            warnings.warn(f"{location} does not contain any files")

    def load(self,repository:Repository, parent_ids:list[str]) -> None:
        """
        Load local leaf components (in the filesystem) into the repository.
        It iterates over subdirectories in the `self.location`, treating each as a separate leaf component, and uses the `ViewFactory` to create a view for it.

        Args:
            repository (Repository): The repository to load components into.
            parent_ids (List[str]): List of parent IDs for the components.
        """
        if not self.location or not os.path.isdir( self.location ):
            return
        for leaf_component_dir in os.listdir( self.location ):
            repository.add( LeafComponent(
                leaf_component_dir,repository,parent_ids,
                ViewFactory.create( "leaf", self.template_info, os.path.join( self.location, leaf_component_dir ), leaf_component_dir )
            ) )

class GirderLeafLoader(LeafLoader):
    """
    Concrete loader for leaf components hosted on a remote Girder server.

    It uses a temporary directory to download the remote content and then delegates
    the actual loading process to a LocalLeafLoader instance.
    """
    def __init__( self, location:str, template_info: TemplateInfo ) -> None:
        """"
        Args:
            location (str): The Girder folder ID or path containing leaf components.
            template_info (Dict[str, Any]): Information about the view template.
        """
        super().__init__( location, template_info )


    def load( self, repository:Repository, parent_ids:List[str] ) -> None:
        """
        Download and load remote (Girder) leaf components into the repository.

        The process involves:
        1. Creating a temporary local directory.
        2. Initializing `GirderHandler` to download the remote folder specified by `self.location` into the temporary directory.
        3. Instantiating a `LocalLeafLoader` to load files from the temporary directory.
        4. Executing the local loader's `load` method.

        Args:
            repository (Repository): The repository to load components into.
            parent_ids (List[str]): List of parent IDs for the components.
        """
        tmpdir = tempfile.mkdtemp()

        girder_handler = GirderHandler( tmpdir )
        girder_handler.downloadFolder( self.location )
        local_loader = LocalLeafLoader( tmpdir, self.template_info )
        local_loader.load( repository, parent_ids )


class LeafLoaderFactory:
    """
    Factory class for creating concrete LeafLoader instances.

    It abstracts the creation logic, allowing the application to request a loader based purely on the configuration metadata.
    """
    @staticmethod
    def create( leaf_config: LeafMetadata ) -> LeafLoader:
        """
        Create a leaf loader based on the configuration metadata.
        It inspects the `platform` field in the configuration to decide whether to return a `LocalLeafLoader` or a `GirderLeafLoader`.

        Args:
            leaf_config (LeafMetadata): The configuration containing the 'platform' ("local" or "girder") and 'path' to the leaf components.
        Returns:
            LeafLoader: An instance of the concrete leaf loader.
        Raises:
            NotImplementedError: If the specified platform is not recognized.
        """
        if leaf_config.path is None:
            warnings.warn("Leaf path is not defined")

        if leaf_config.platform == "local":
            return LocalLeafLoader( leaf_config.path, leaf_config.template_info )
        elif leaf_config.platform == "girder":
            return GirderLeafLoader( leaf_config.path, leaf_config.template_info )
        else:
            raise NotImplementedError("Remote locations not yet implemented")

