from jinja2 import Environment, FileSystemLoader

class Renderer:
    """ Base Class to render the JSON files to AsciiDoc files using Jinja2 templates"""

    def __init__(self, template_path):
        """ Initialize the template for the renderer
        Args:
            template_path (str): The path to the Jinja2 template
        """
        env = Environment(loader=FileSystemLoader("."), trim_blocks=True, lstrip_blocks=True)
        self.template = env.get_template(template_path)

    def render(self, output_filepath, data):
        """ Render the JSON file to an AsciiDoc file using a Jinja2 template and the given data"""
        with open(output_filepath, 'w') as f:
            f.write(self.template.render(data))

