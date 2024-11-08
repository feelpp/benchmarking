import json, os, re
from pydantic import BaseModel

class TemplateProcessor:
    """Helper class for processing template values in a JSON file"""
    def __init__(self):
        self.template_pattern = re.compile(r'{{([^{}]+)}}')

    @staticmethod
    def flattenDict(nested_json, parent_key='', separator='.'):
        """Flattens a nested JSON-like dictionary.
        Args:
            nested_json (dict): The JSON-like dictionary to flatten. It can be a pydantic model
            parent_key (str): A string representing the prefix for keys in nested levels (used internally in recursion).
            separator (str): The separator string to use between keys from different levels. Default is '.'.

        Returns:
            dict: A flattened dictionary where nested keys are joined by the separator.
        """
        items = []
        if isinstance(nested_json,BaseModel):
            nested_dict = nested_json.model_dump()
        else:
            nested_dict = nested_json
        for key, value in nested_dict.items():
            new_key = f"{parent_key}{separator}{key}" if parent_key else key
            if isinstance(value, dict):
                items.extend(TemplateProcessor.flattenDict(value, new_key, separator=separator).items())
            elif isinstance(value, list):
                for index, item in enumerate(value):
                    if isinstance(item,dict) or isinstance(item, list):
                        items.extend(TemplateProcessor.flattenDict(item, f"{new_key}{separator}{index}", separator=separator).items())
                    else:
                        items.append((f"{new_key}{separator}{index}", item))
            else:
                items.append((new_key, value))
        return dict(items)

    def replacePlaceholders(self,target,flattened_source):
        def replaceMatch(match):
            resolved = flattened_source.get(match.group(1).strip(),match.group(0))
            if match.group(1) in flattened_source:
                if isinstance(resolved,str) and "{{" in resolved and "}}" in resolved:
                    resolved = self.replacePlaceholders(resolved,flattened_source)
            return resolved

        replaced = self.template_pattern.sub(replaceMatch,target)

        return os.path.expandvars(replaced) if "$" in replaced else replaced


    def recursiveReplace(self,target,flattened_source):
        if isinstance(target, dict):
            return {k: self.recursiveReplace(v,flattened_source) for k, v in target.items()}
        elif isinstance(target,list):
            return [self.recursiveReplace(v,flattened_source) for v in target]
        elif isinstance(target, str):
            return self.replacePlaceholders(target,flattened_source)
        return target


class ConfigReader:
    """ Class to load config files"""
    def __init__(self, config_path, schema):
        """
        Args:
            config_path (str) : Path to the config JSON file
        """
        self.schema = schema
        self.config = self.load(config_path, schema)
        self.processor = TemplateProcessor()

    def load(self,config_path, schema):
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
            self.config = schema(**self.config)
        return self.config

    def updateConfig(self, flattened_replace = None):
        """ Recursively replace all placeholders {{}} on the config.
        Args:
            flattened_replace: (dict) Containing all key, pair values that indicate the paths to replace. e.g { "replace.this.path": "with_this_value" }
                If not provided, placeholders will be changed with own confing
        """
        if not flattened_replace:
            flattened_replace = self.processor.flattenDict(self.config.model_dump())
        self.config = self.schema(**self.processor.recursiveReplace(self.config.model_dump(),flattened_replace))

    def __repr__(self):
        return json.dumps(self.config.dict(), indent=4)