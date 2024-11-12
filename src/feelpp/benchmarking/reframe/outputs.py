import reframe.utility.sanity as sn
import os, re, shutil


class OutputsHandler:
    """Class to handle application outputs and convert them to reframe readable objects"""
    def __init__(self,outputs_config,additional_files_config = None):
        self.config = outputs_config
        self.additional_files_config = additional_files_config

    def getOutputs(self):
        """ Opens and parses the all the outputs files provided on the configuration
        Returns:
            dict[str,performance_function] : Dictionary with deferrable functions containing the value of the outputs.
        """
        rfm_outputs = {}
        for output_info in self.config:
            if output_info.format == "csv":
                number_regex = re.compile(r'^-?\d+(\.\d+)?([eE][-+]?\d+)?$')
                rows = sn.extractall(
                    r'^(?!\s*$)(.*?)[\s\r\n]*$',
                    output_info.filepath,
                    0,
                    conv=lambda x: [float(col.strip()) if number_regex.match(col.strip()) else col.strip() for col in x.split(',') if col.strip()]
                )
                header = rows[0]
                rows = rows[1:]

                assert all ( len(header.evaluate()) == len(row) for row in rows), f"CSV File {output_info.filepath} is incorrectly formatted"

                for line in range(len(rows.evaluate())):
                    for i,col in enumerate(header):
                        rfm_outputs.update({ f"{col}" : sn.make_performance_function(rows[line][i],unit="") })
            else:
                raise NotImplementedError(f"Output extraction not implemented for format {output_info.format}")

        return rfm_outputs

    def copyDescription(self,dir_path):
        pass

    def copyParametrizedDescriptions(self,dir_path,name):
        """ Searches the files on the additional_files.parameterized_descriptions_filepath configuration and copy them inside dir_path/partials
        Args:
            dir_path (str) : Directory where the reframe report is exported to
            name(str): name of the new file (without extension)
        """

        if self.additional_files_config and self.additional_files_config.parameterized_descriptions_filepath:
            file_extension = self.parameterized_descriptions_filepath.split(".")[-1]

            outdir = os.path.join(dir_path,"parametrized_partials")
            filename = f"{name}.{file_extension}"

            if not os.path.exists(outdir):
                os.mkdir(outdir)

            shutil.copy2( self.parameterized_descriptions_filepath, os.path.join(outdir,filename) )

