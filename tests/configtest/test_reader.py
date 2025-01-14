""" tests for the configReader module"""

import pytest, os,tempfile, json
from feelpp.benchmarking.reframe.config.configReader import ConfigReader, TemplateProcessor
from pydantic import BaseModel, field_validator
from typing import Optional, Dict
from unittest.mock import mock_open, patch, MagicMock

class SampleModel(BaseModel):
    field1: str
    field2: int
    nested: dict

class TestTemplateProcessor:
    """Tests for the TemplateProcessor class"""

    @pytest.mark.parametrize( "nested_json, parent_key, separator, expected",[
        # Case 1: Simple flat dictionary with default separator ('.')
        ({"key1": "value1", "key2": "value2"}, "", ".", {"key1": "value1", "key2": "value2"}),

        # Case 2: Nested dictionary with default separator ('.')
        ({"key1": "value1", "nested": {"subkey1": "subvalue1", "subkey2": "subvalue2"}},
         "", ".", {"key1": "value1", "nested.subkey1": "subvalue1", "nested.subkey2": "subvalue2"}),

        # Case 3: Nested dictionary with custom separator ('_')
        ({"key1": "value1", "nested": {"subkey1": "subvalue1", "subkey2": "subvalue2"}},
         "", "_", {"key1": "value1", "nested_subkey1": "subvalue1", "nested_subkey2": "subvalue2"}),

        # Case 4: Parent key with separator
        ({"key1": "value1", "nested": {"subkey1": "subvalue1", "subkey2": "subvalue2"}},
         "parent", ".", {"parent.key1": "value1", "parent.nested.subkey1": "subvalue1", "parent.nested.subkey2": "subvalue2"}),

        # Case 5: Empty dictionary (should return empty dictionary)
        ({}, "", ".", {}),

        # Case 6: Nested dictionary with a list, using default separator
        ({"key1": "value1", "list": [{"subkey1": "subvalue1"}, {"subkey2": "subvalue2"}]},
         "", ".", {"key1": "value1", "list.0.subkey1": "subvalue1", "list.1.subkey2": "subvalue2"}),

        # Case 7: Nested dictionary with a list and custom separator
        ({"key1": "value1", "list": [{"subkey1": "subvalue1"}, {"subkey2": "subvalue2"}]},
         "", "_", {"key1": "value1", "list_0_subkey1": "subvalue1", "list_1_subkey2": "subvalue2"}),

        # Case 8: Mixed data types (strings, integers, lists)
        ({"key1": "value1", "key2": 42, "list": [1, 2]}, "", ".", {"key1": "value1", "key2": 42, "list.0": 1, "list.1": 2}),

        # Case 9: Flattening a Pydantic model (BaseModel)
        (SampleModel(field1="test", field2=5, nested={"innerKey": "innerValue"}), "", ".",
         {"field1": "test", "field2": 5, "nested.innerKey": "innerValue"}),

        # Case 10: Nested structure with empty list
        ({"key1": "value1", "list": []}, "", ".", {"key1": "value1"}),

        # Case 11: Nested structure with empty dictionary
        ({"key1": "value1", "nested": {}}, "", ".", {"key1": "value1"}),

        # Case 12: Separator with special characters
        ({"key1": "value1", "nested": {"subkey1": "subvalue1", "subkey2": "subvalue2"}},
         "", "~~", {"key1": "value1", "nested~~subkey1": "subvalue1", "nested~~subkey2": "subvalue2"}),

        # Case 13: Complex nested dictionary with multiple levels and custom separator
        ({"level1": {"level2": {"level3": "value"}}}, "", "|", {"level1|level2|level3": "value"})
    ])
    def test_flattenDict(self, nested_json, expected,separator,parent_key):
        """Tests for the flattenDict method of the TemplateProcessor class.
        It compares a the result of the function for a given nested_json to the corresponding expected result, for a variaty of separators and parent keys """
        result = TemplateProcessor.flattenDict(nested_json,parent_key=parent_key,separator=separator)
        assert result == expected

    @pytest.mark.parametrize("target,flattened_source,expected", [
        # Case 1: Basic placeholder replacement
        ("Hello, {{name}}!", {"name": "Alice"}, "Hello, Alice!"),

        # Case 2: Missing key (should return the original placeholder)
        ("Hello, {{name}}!", {}, "Hello, {{name}}!"),

        # Case 3: Recursive placeholder replacement
        ("Hello, {{greeting}}!", {"greeting": "{{name}}", "name": "Alice"}, "Hello, Alice!"),

        # Case 4: Environment variable replacement (e.g., $HOME)
        ("$HOME", {}, os.path.expandvars("$HOME")),

        # Case 5: Nested placeholders (recursive replacement)
        ("Your id is {{user.id}} and name is {{user.name}}",
         {"user.id": "123", "user.name": "Alice"},
         "Your id is 123 and name is Alice"),

        # Case 6: Missing nested key (should leave placeholder intact)
        ("Your id is {{user.id}}", {"user.name": "Alice"}, "Your id is {{user.id}}"),

        # Case 7: No placeholders (should return the original string)
        ("Hello, world!", {"name": "Alice"}, "Hello, world!"),

        # Case 8: Multiple placeholders in one string
        ("{{greeting}}, {{name}}!", {"greeting": "Hello", "name": "Alice"}, "Hello, Alice!"),

        # Case 9: Placeholders that reference other placeholders
        ("{{greeting}} {{name}}!", {"greeting": "{{title}}", "name": "Alice", "title": "Mr."},
         "Mr. Alice!"),

        # Case 10: Placeholders with spaces and special characters
        ("{{ user.name }} is a {{ user.role }}", {"user.name": "Alice", "user.role": "Admin"},
         "Alice is a Admin"),

        # Case 11: Placeholders with missing value (should return original placeholder)
        ("{{user.name}} is {{user.role}}", {"user.name": "Alice"}, "Alice is {{user.role}}"),

        # Case 12: Handling of special characters in placeholder names (e.g., 'var_1')
        ("{{var_1}}", {"var_1": "value"}, "value"),

        # Case 13: Placeholder with embedded environment variable
        ("User home directory is $HOME", {}, f"User home directory is {os.path.expandvars('$HOME')}"),

        # Case 1: Simple Nested Recursive Placeholder
        ( "My recursive nested placeholder is {{x.{{a.b}}.y}}", { "a.b": "c","x.c.y": "z"},"My recursive nested placeholder is z"),

        # Case 2: Deeply Nested Placeholders
        ("The final result is {{x.{{y.{{a.b}}}}}}",{"a.b": "c","y.c": "x","x.x": "y","x.y": "z"},"The final result is y"),

        # Case 3: Deeply Nested Placeholders Not found
        ("The final result is {{x.{{y.{{a.b}}}}}}",{"a.b": "c","y.c": "x","x.z": "y","x.y": "z"},"The final result is {{x.x}}"),

        # Case 4: Circular Placeholder (Should remain unchanged)
        # For this case, we want to test what happens if a recursive cycle is formed
        ("This is a circular placeholder: {{a.{{a}}}}",{"a": "{{a}}"},"This is a circular placeholder: {{a.{{a}}}}")
    ])
    def test_replacePlaceholders(self, target, flattened_source, expected, monkeypatch):
        """Tests for the replacePlaceholders method of the TemplateProcessor class.
        It compares a the result of the function for a given target and flattened source to see if placeholders where correctly replaced.
        """

        processor = TemplateProcessor()
        if "$HOME" in expected:
            monkeypatch.setenv("HOME", "/home/user")
        result = processor.replacePlaceholders(target, flattened_source)
        assert result == expected


    @pytest.mark.parametrize(
        "input_data, flattened_source, expected_output", [
            # Case 1: Simple Dictionary Replacement
            ( {"user": {"name": "{{user.name}}", "age": "{{user.age}}"}}, {"user.name": "John", "user.age": "30"}, {"user": {"name": "John", "age": "30"}} ),

            # Case 2: Nested Dictionary Replacement
            ( {"user": { "name": "{{user.name}}", "address": { "city": "{{user.address.city}}", "zip": "{{user.address.zip}}" } } }, { "user.name": "Alice", "user.address.city": "Wonderland", "user.address.zip": "12345" }, { "user": { "name": "Alice", "address": { "city": "Wonderland", "zip": "12345" }}} ),

            # Case 3: List Input
            ({"items": ["{{item1}}", "{{item2}}"]},{"item1": "apple", "item2": "banana"},{"items": ["apple", "banana"]}),

            # Case 4: List with Nested Dictionaries
            ({"items": [{"name": "{{item.name}}", "category": "{{item.category}}"}]},{"item.name": "apple", "item.category": "fruit"},{"items": [{"name": "apple", "category": "fruit"}]}),

            # Case 5: Mixed Dictionary and List Input
            ({"user": {"name": "{{user.name}}","addresses": [{"city": "{{user.address.city}}", "zip": "{{user.address.zip}}"},{"city": "{{user.address.city}}", "zip": "{{user.address.zip}}"}]}},{"user.name": "Alice","user.address.city": "Wonderland","user.address.zip": "12345"},{"user": {"name": "Alice","addresses": [{"city": "Wonderland", "zip": "12345"},{"city": "Wonderland", "zip": "12345"}]}}),

            # Case 6: No Placeholders
            ({"message": "Hello, world!"},{"user.name": "John"},{"message": "Hello, world!"}),

        ]
    )
    def test_recursiveReplace(self,input_data, flattened_source, expected_output):
        """Tests for the recursiveReplace method of the TemplateProcessor class.
        It compares a the result of the function for a given target and flattened source to see if placeholders where correctly replaced for dictionaries
        """
        processor = TemplateProcessor()
        result = processor.recursiveReplace(input_data, flattened_source)
        assert result == expected_output


class MockConfigFile(BaseModel):
    field1: str
    field2: int
    field3: float
    field4: Optional[Dict] = {}

    @field_validator("field1",mode="before")
    @classmethod
    def dryRunMode(cls,v,info):
        if info.context and info.context.get("dry_run",False):
            v = "dry value"
        return v

    mock_merge_field: Optional[str] = None

class TestConfigReader:
    """Tests for the ConfigReader class"""

    def initConfig(self,configs,dry_run):
        """ Helper function to initialize the configReader"""
        files = []
        for config in configs:
            temp = tempfile.NamedTemporaryFile()
            with open(temp.name,'w') as f:
                f.write(config)
            files.append(temp)

        config_reader = ConfigReader([f.name for f in files], MockConfigFile, dry_run)
        for f in files:
            f.close()

        return config_reader

    @pytest.mark.parametrize(("configs","dry_run","expected"),[
        #Basic test : single file
        (['{"field1":"value1","field2":2,"field3":0.3,"field4":{"a":5}}'],False,MockConfigFile(field1="value1",field2=2,field3=0.3,field4={"a":5})),

        #Single file optional field
        (['{"field1":"value1","field2":2,"field3":0.3}'],False,MockConfigFile(field1="value1",field2=2,field3=0.3,field4={})),

        #Single file with comments
        (['{"field1":"value1",\n//This is a C-style comment\n"field2":2,"field3":0.3}'],False,MockConfigFile(field1="value1",field2=2,field3=0.3,field4={})),

        #Multiple file merge
        (['{"field1":"value1","field2":2,"field3":0.3}','{"mock_merge_field":"mock val"}'],False,MockConfigFile(field1="value1",field2=2,field3=0.3,field4={},mock_merge_field="mock val")),

        #Dry-run, context aware
        (['{"field1":"value1","field2":2,"field3":0.3}'],True,MockConfigFile(field1="dry value",field2=2,field3=0.3,field4={}))
    ])
    def test_init(self,configs,dry_run,expected):
        """Tests the class instantiation. And the load method more precisely"""
        config_reader = self.initConfig(configs,dry_run)
        assert config_reader.config == expected

    @pytest.mark.parametrize(("initial_configs","flattened_replace","expected"),[
    # Test updateConfig on single file
        #Simple external replace
        (['{"field1":"Value from rep_field: {{rep_field}}", "field2":2, "field3":0.3}'],{"rep_field": "test value"},MockConfigFile(field1="Value from rep_field: test value",field2=2,field3=0.3)),

        #Nested external replace
        (['{"field1":"Value from rep_field: {{rep_field.value}}", "field2":2, "field3":0.3}'],{"rep_field.value": "test value"},MockConfigFile(field1="Value from rep_field: test value",field2=2,field3=0.3)),

        #Self replace test
        (['{"field1":"Value from field2: {{field2}}", "field2":2, "field3":0.3}'],None,MockConfigFile(field1="Value from field2: 2",field2=2,field3=0.3)),

    ])
    def test_updateConfig(self,initial_configs,flattened_replace,expected):
        """Tests the updateConfig method of ConfigReader"""
        config_reader = self.initConfig(initial_configs,dry_run=False)
        config_reader.updateConfig(flattened_replace=flattened_replace)
        assert config_reader.config == expected
