import json
import glob
from jinja2 import Environment, FileSystemLoader

# Setup Jinja2 environment
env = Environment(loader=FileSystemLoader('.'), trim_blocks=True, lstrip_blocks=True)

def convert_hostname(hostname):
    if hostname.startswith("mel"):
        return "meluxina"
    if "karolina"  in hostname:
        return "karolina"
    if "discoverer" in hostname:
        return "discoverer"
    # You can add more rules here if needed
    return hostname

for module in ['meluxina', 'karolina', 'discoverer']:
    # Path to the JSON files
    json_files_path = f'{module}/pages/kub/scenario0/*.json'

    # Iterate over each JSON file in the directory
    for json_file in glob.glob(json_files_path):
        # Load JSON data
        with open(json_file, 'r') as file:
            data = json.load(file)

        # Add the custom filter to the Jinja2 environment
        env.filters['convert_hostname'] = convert_hostname

        # Load the Jinja2 template
        template = env.get_template('template.adoc.j2')

        data['filename'] = json_file

        # Render the template with data
        output = template.render(data)

        # Define the output file name (based on the JSON file name)
        output_file_name = f'{module}/pages/output_' + \
            json_file.split('/')[-1].replace('.json', '.adoc')

        # Write the output to a file
        with open(output_file_name, 'w') as file:
            file.write(output)
