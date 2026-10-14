project = 'manim'
copyright = '- This document has been placed in the public domain.'
author = 'TonyCrane'

release = ''

extensions = [
    'sphinx.ext.githubpages',
    'sphinx_copybutton'
]

source_suffix = '.rst'
master_doc = 'index'
pygments_style = 'default'

html_static_path = ["_static"]
html_css_files = [
    "https://cdn.jsdelivr.net/gh/manim-kindergarten/CDN@master/manimgl_assets/custom.css", 
    "https://cdn.jsdelivr.net/gh/manim-kindergarten/CDN@master/manimgl_assets/colors.css"
]
html_theme = 'furo'
html_favicon = '_static/icon.png'
html_logo = '../../logo/transparent_graph.png'
html_theme_options = {
    "sidebar_hide_name": True,
}
