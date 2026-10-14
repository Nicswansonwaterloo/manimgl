CLI flags and configuration
===========================

Command line
------------

Run a scene with a path to its Python file and its class name:

.. code-block:: sh

    manimgl path/to/scenes.py SceneName

``manim-render`` is an alias for ``manimgl``. With multiple scenes and no
class name, ManimGL prompts you to choose one.

Common flags:

- ``-w`` writes a video.
- ``-o`` writes the result and opens it.
- ``-s`` skips animations to show the final frame; combine with ``-w`` or
  ``-o`` to save an image.
- ``-l`` renders at 480p; ``-m`` renders at 720p.
- ``-n START[,END]`` starts at an animation index and optionally stops
  before a second index.
- ``-r WIDTHxHEIGHT`` sets the resolution, and ``--fps FPS`` sets the frame rate.
- ``--video_dir PATH`` selects the output directory for videos and images.

Get the complete list from the installed CLI:

.. code-block:: sh

    manimgl --help

Configuration files
-------------------

Create ``custom_config.yml`` in the directory from which you run ManimGL.
Only include settings you want to override. Defaults are loaded from
``manimlib/default_config.yml``, followed by the working directory's
``custom_config.yml``, then a file supplied with ``--config_file``.
CLI options override the corresponding settings. Loading a custom file
does not modify the defaults on disk.

For example:

.. code-block:: yaml

    directories:
      subdirs:
        output: "renders"
    camera:
      background_color: "#222222"
      fps: 30

Both videos and final-frame images will be written under ``renders/``.
To use a configuration file at another path:

.. code-block:: sh

    manimgl path/to/scenes.py SceneName --config_file path/to/config.yml

The defaults below document the available settings alongside their values:

.. literalinclude:: ../../../manimlib/default_config.yml
   :language: yaml
