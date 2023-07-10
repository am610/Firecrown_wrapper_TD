# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import recommonmark
from recommonmark.transform import AutoStructify

extensions = ['recommonmark']

# At the bottom of the file
def setup(app):
    app.add_config_value('recommonmark_config', {
            'auto_toc_tree_section': 'Contents',
            }, True)
    app.add_transform(AutoStructify)

    
# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Firecrown_Wrapper_Time_Domain'
copyright = '2023, Ayan Mitra'
author = 'Ayan Mitra'
release = "'1.1'"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
