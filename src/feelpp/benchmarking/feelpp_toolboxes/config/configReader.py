import json, sys, os
from feelpp.benchmarking.feelpp_toolboxes.config.configSchema import ConfigFile



#https://stackoverflow.com/questions/6760685/what-is-the-best-way-of-implementing-singleton-in-python
class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        else:
            cls._instances[cls].__init__(*args, **kwargs)
        return cls._instances[cls]


class ConfigReader(metaclass=Singleton):
    """ Singleton class to load config files"""
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