import json, os

class ConfigReader:
    """ Class to load config files"""
    def __init__(self, config_path, schema):
        """
        Args:
            config_path (str) : Path to the config JSON file
        """
        if not hasattr(self,"config"):
            self.config = self.load(config_path, schema)

    def load(self,config_path, schema):
        """ Loads the JSON file and checks if the file exists.
        Args:
            config_path (str) : Path to the config JSON file
            schema (cls) : The pydantic schema to validate the data
        """
        assert os.path.exists(config_path), f"Cannot find config file {config_path}"
        with open(config_path, "r") as cfg:
            config = schema(**json.load(cfg))
        return config

    def __repr__(self):
        return json.dumps(self.config, indent=4)