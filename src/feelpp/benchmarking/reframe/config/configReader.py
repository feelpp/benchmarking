import json, os, re
from feelpp.benchmarking.report.config.handlers import GirderHandler

class ConfigReader:
    """ Class to load config files"""
    def __init__(self, config_path, schema):
        """
        Args:
            config_path (str) : Path to the config JSON file
        """
        if config_path.startswith("girder:"):
            girder_meta = json.loads(config_path.replace("girder:",""))
            self.config = self.loadGirder(girder_meta, schema)
        elif config_path.startswith("github:"):
            raise NotImplementedError("Github input not implemented")
        else:
            self.config = self.loadLocal(config_path, schema)

    def loadGirder(self,metadata,schema):
        """ Loads a configuration file from Girder, creating a temporary file on disk
        Args:
            metadata (dict): Dictionary describing needed arguments to download a girder object
                Must be in the form of {'file': file_id, 'api_key': your_key}
        """
        assert "file" in metadata, "girder file argument not found"
        assert "api_key" in metadata, "girder api key argument not found"

        tmp_name = "tmp_config.json"
        os.environ["GIRDER_API_KEY"] = os.path.expandvars(metadata["api_key"])
        gc = GirderHandler("./config")
        gc.downloadFile(metadata["file"],name=tmp_name)

        config = self.loadLocal(os.path.join("./config/",tmp_name), schema)

        os.remove(os.path.join("./config/",tmp_name))

        return config

    def loadLocal(self,config_path, schema):
        """ Loads the JSON file and checks if the file exists.
        Args:
            config_path (str) : Path to the config JSON file
            schema (cls) : The pydantic schema to validate the data
        Returns:
            Schema : parsed and validated configuration
        """
        assert os.path.exists(os.path.abspath(config_path)), f"Cannot find config file {config_path}"
        with open(config_path, "r") as cfg:
            self.config = json.load(cfg)
            self.config = self.recursiveReplace(self.config)
            self.config = schema(**self.config)
        return self.config

    def getNestedValue(self,data,path):
        """Helper function to get a value from a nested dictionary using a dot-separated path.
        Args:
            data (dict): The dictionary to search
            path (str): The dot-separated path (e.g., "field1.field1_2.field1_2_1")
        Returns:
            The value from the nested dictionary, or the placeholder itself if not found
        """
        keys = path.split(".")
        for key in keys:
            if isinstance(data, dict) and key in data:
                data = data[key]
            else:
                # If the key is not found, return the placeholder itself
                return "{{" + path + "}}"
        return data

    def recursiveReplace(self,data):
        """ Replaces template with the actual value if found inside the json. Else, the placeholder is left as it was.
            data (dict): The initial json data with templates
        Returns:
            dict: Replaced data
        """
        if isinstance(data, dict):
            return {k: self.recursiveReplace(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.recursiveReplace(v) for v in data]
        elif isinstance(data, str):
            # Find placeholders in the form {nested.field.path}
            rep = re.sub(r"\{\{([\w\.]+)\}\}", lambda match: str(self.getNestedValue(self.config, match.group(1))), data)
            if "$" in rep:
                rep = os.path.expandvars(rep)
            return rep
        return data

    def __repr__(self):
        return json.dumps(self.config.dict(), indent=4)