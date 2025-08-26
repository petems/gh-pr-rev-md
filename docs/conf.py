# Configuration file for the Sphinx documentation builder.

import os
import sys
from datetime import datetime

# Add project root to sys.path if needed
sys.path.insert(0, os.path.abspath('..'))

project = 'gh-pr-rev-md'
author = 'Peter Souter'
current_year = datetime.now().year
copyright = f'{current_year}, {author}'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']
exclude_patterns = []

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# Autodoc options
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
}
