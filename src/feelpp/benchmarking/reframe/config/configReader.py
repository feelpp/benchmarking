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

    def replacePlaceholders(self,target,flattened_source,processed_placeholders=None):
        if processed_placeholders is None:
            processed_placeholders = set()

        def replaceMatch(match):
            placeholder = match.group(1).strip()

            if placeholder in processed_placeholders:
                return match.group(0)

            processed_placeholders.add(placeholder)
            resolved = flattened_source.get(match.group(1).strip(),match.group(0))

            if match.group(1) in flattened_source:
                if isinstance(resolved,str) and "{{" in resolved and "}}" in resolved:
                    resolved = self.replacePlaceholders(resolved,flattened_source,processed_placeholders)
            return resolved

        previous_target = None
        while target != previous_target:
            previous_target = target
            target = self.template_pattern.sub(replaceMatch, target)

        return os.path.expandvars(target) if "$" in target else target


    def recursiveReplace(self,target,flattened_source):
        if isinstance(target, dict):
            return {k: self.recursiveReplace(v,flattened_source) for k, v in target.items()}
        elif isinstance(target,list):
            return [self.recursiveReplace(v,flattened_source) for v in target]
        elif isinstance(target, str):
            return self.replacePlaceholders(target,flattened_source)
        return target


# https://stackoverflow.com/questions/29959191/how-to-parse-json-file-with-c-style-comments
class JSONWithCommentsDecoder(json.JSONDecoder):
    def __init__(self, **kw):
        super().__init__(**kw)

    def decode(self, s: str):
        s = '\n'.join(l if not l.lstrip().startswith('//') else '' for l in s.split('\n'))
        return super().decode(s)

class ConfigReader:
    """ Class to load config files"""
    def __init__(self, config_paths, schema, dry_run=False):
        """
        Args:
            config_paths (str | list[str]) : Path to the config JSON file. If a list is provided, files will be merged.
        """
        self.schema = schema
        self.context = {
            "dry_run":dry_run
        }
        self.config = self.load(
            config_paths if type(config_paths) == list else [config_paths],
            schema
        )
        self.processor = TemplateProcessor()

    def load(self,config_paths, schema):
        """ Loads the JSON file and checks if the file exists.
        Args:
            config_paths (list[str]) : Paths to the config JSON files to merge
            schema (cls) : The pydantic schema to validate the data
        Returns:
            Schema : parsed and validated configuration
        """

        self.config = {}
        for config in config_paths:
            assert os.path.exists(os.path.abspath(config)), f"Cannot find config file {config}"
            with open(config, "r") as cfg:
                self.config.update(json.load(cfg, cls=JSONWithCommentsDecoder))

        self.config = schema.model_validate(self.config, context=self.context)

        return self.config

    def updateConfig(self, flattened_replace = None):
        """ Recursively replace all placeholders {{}} on the config.
        Args:
            flattened_replace: (dict) Containing all key, pair values that indicate the paths to replace. e.g { "replace.this.path": "with_this_value" }
                If not provided, placeholders will be changed with own confing
        """
        if not flattened_replace:
            flattened_replace = self.processor.flattenDict(self.config.model_dump())
        self.config = self.schema.model_validate(self.processor.recursiveReplace(self.config.model_dump(),flattened_replace), context=self.context)

    def __repr__(self):
        return json.dumps(self.config.dict(), indent=4)