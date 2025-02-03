import reframe.utility.sanity as sn
import os, re, shutil


class OutputsHandler:
    """Class to handle application outputs and convert them to reframe readable objects"""
    def __init__(self,additional_files_config = None):
        self.additional_files_config = additional_files_config


    def copyDescription(self,dir_path, name): #TODO: This can be redesigned... or factor it at least
        """ Searches the file on the additional_files.description_filepath configuration and copies it inside dir_path/partials
        Args:
            dir_path (str) : Directory where the reframe report is exported to
            name(str): name of the new file (without extension)
        """
        if self.additional_files_config and self.additional_files_config.description_filepath:
            file_extension = self.additional_files_config.description_filepath.split(".")[-1] if "." in self.additional_files_config.description_filepath else None

            outdir = os.path.join(dir_path,"partials")
            if not os.path.exists(outdir):
                os.mkdir(outdir)

            filename = f"{name}.{file_extension}" if file_extension else name

            shutil.copy2( self.additional_files_config.description_filepath, os.path.join(outdir,filename) )



    def copyParametrizedDescriptions(self,dir_path,name):
        """ Searches the files on the additional_files.parameterized_descriptions_filepath configuration and copy them inside dir_path/partials
        Args:
            dir_path (str) : Directory where the reframe report is exported to
            name(str): name of the new file (without extension)
        """

        if self.additional_files_config and self.additional_files_config.parameterized_descriptions_filepath:
            file_extension = self.additional_files_config.parameterized_descriptions_filepath.split(".")[-1] if "." in self.additional_files_config.parameterized_descriptions_filepath else None

            outdir = os.path.join(dir_path,"partials")
            if not os.path.exists(outdir):
                os.mkdir(outdir)

            filename = f"{name}.{file_extension}" if file_extension else name

            shutil.copy2( self.additional_files_config.parameterized_descriptions_filepath, os.path.join(outdir,filename) )

