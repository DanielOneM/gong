import os

from jinja2 import Environment, FileSystemLoader


template_path = os.path.join(os.path.dirname(__file__), 'templates')
jinja = Environment(loader=FileSystemLoader(template_path))
