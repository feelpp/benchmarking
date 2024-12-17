"""Tests related to girder """

from feelpp.benchmarking.report.config.handlers import GirderHandler
import pytest
import os, tempfile
from requests.exceptions import HTTPError

class TestGirderHandler:
    """Tests for the GirderHandler class"""
    handler = GirderHandler(download_base_dir="./tests/data/outputs")

    def test_initClient(self):
        """Tests girder client initialization"""
        assert os.environ.get("GIRDER_API_KEY",False), "GIRDER API KEY NOT SET"

        print(dir(self.handler.client))
        assert os.path.normpath(self.handler.client.urlBase) == os.path.normpath(self.handler.base_url), "Wrong url"
        assert self.handler.client.getServerVersion() is not None

    def test_downloadFile(self):
        """Tests the downloadFile method
        Checks that a test file is correctly downloaded to the expected location
        Checks that an error is thrown if the requested ressource is not a file or not found
        """
        with tempfile.TemporaryDirectory(dir=self.handler.download_base_dir) as tmp_dir:
            test_file_id = "676155404c9ccbdde21a4bf1"
            self.handler.downloadFile(file_id=test_file_id,output_dir=os.path.basename(tmp_dir),name="custom_name")

            assert os.path.isfile(os.path.join(self.handler.download_base_dir,os.path.basename(tmp_dir),"custom_name"))

            unkown_id = "abcdefg"
            with pytest.raises(HTTPError,match="400"):
                self.handler.downloadFile(file_id=unkown_id,output_dir=os.path.basename(tmp_dir))

            not_a_file_id = "676154ff4c9ccbdde21a4bee"
            with pytest.raises(HTTPError,match="400"):
                self.handler.downloadFile(file_id=not_a_file_id,output_dir=os.path.basename(tmp_dir))

    def test_downloadFolder(self):
        """Tests the downloadFolder method
        Checks that a folder is downloaded recursively to the expected location
        """

        test_folder_id = "676157a44c9ccbdde21a4bf2"
        with tempfile.TemporaryDirectory(dir=self.handler.download_base_dir) as tmp_dir:
            files = self.handler.downloadFolder(folder_id=test_folder_id,output_dir=os.path.basename(tmp_dir))
            assert "testfile" in files and "testfile (1)" in files

            assert os.path.isdir(os.path.join(self.handler.download_base_dir,os.path.basename(tmp_dir)))
            assert os.path.isfile(os.path.join(self.handler.download_base_dir,os.path.basename(tmp_dir),"testfile","TEST FILE"))
            assert os.path.isfile(os.path.join(self.handler.download_base_dir,os.path.basename(tmp_dir),"testfile (1)","TEST FILE"))

    def test_listChildren(self):
        """Tests the listChildren method
        Checks that subfolders and files are correctly listed
        Checks that an exception is raised when a children is not found"""

        test_folder_id = "676157a44c9ccbdde21a4bf2"
        children = self.handler.listChildren(parent_id=test_folder_id)
        assert "testfile" in [c["name"] for c in children]
        assert "testfile (1)" in [c["name"] for c in children]


        children = self.handler.listChildren(parent_id=test_folder_id, children_name="testfile")
        assert children["name"] == "testfile"

        #Non existant children
        with pytest.raises(AssertionError, match="File not Found in Girder with the name "):
            children = self.handler.listChildren(parent_id=test_folder_id, children_name="unkown_children")

    def test_upload(self):
        """Tests uploading ressources to girder"""
        pass #TODO