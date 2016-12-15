import os

from jinja2 import Environment, FileSystemLoader


template_path = os.path.join(os.path.dirname(__file__),'templates')
print template_path
jinja = Environment(loader=FileSystemLoader(template_path))