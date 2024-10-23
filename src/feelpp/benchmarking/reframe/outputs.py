import reframe.utility.sanity as sn
import os, re


class OutputsHandler:
    """Class to handle application outputs and convert them to reframe readable objects"""
    def __init__(self,outputs_config):
        self.config = outputs_config

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
