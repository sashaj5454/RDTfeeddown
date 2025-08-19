# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
from pathlib import Path

project = "RDTfeeddown"
copyright = "2025, Sasha Horney"  # noqa: A001
author = "Sasha Horney"
release = "0.0.0"

sys.path.insert(0, os.path.abspath("../src"))
sys.path.append(str(Path("source/_ext").resolve()))
# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosectionlabel",
    "role",
]

templates_path = ["source/_templates"]
exclude_patterns = []
autosectionlabel_prefix_document = True

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["source/_static"]
html_css_files = ["custom.css"]

rst_prolog = """
.. role:: orange
   :class: orange
.. role:: skyblue
   :class: skyblue
.. role:: green
   :class: green
.. role:: yellow
   :class: yellow
.. role:: blue
   :class: blue
.. role:: vermilion
   :class: vermilion
.. role:: pink 
   :class: pink
.. role:: grey
   :class: grey
"""
