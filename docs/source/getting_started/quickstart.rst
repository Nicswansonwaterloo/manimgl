Quick start
===========

Install this checkout using the
`repository README <https://github.com/3b1b/manim#installation>`_.
ManimGL uses the ``manimgl`` package and ``from manimlib import *``;
Manim Community is a separate project with different APIs.

Create a scene
--------------

Save the following as ``start.py``:

.. code-block:: python

    from manimlib import *

    class SquareToCircle(Scene):
        def construct(self):
            square = Square()
            circle = Circle(fill_color=BLUE, fill_opacity=0.5)
            self.play(ShowCreation(square))
            self.play(ReplacementTransform(square, circle))
            self.wait()

A scene's ``construct`` method defines its objects and animations.
``self.play`` runs an animation, and ``self.wait`` pauses the scene.

Preview the scene in a window:

.. code-block:: sh

    manimgl start.py SquareToCircle

Save a video, or save just the final frame:

.. code-block:: sh

    manimgl start.py SquareToCircle -w
    manimgl start.py SquareToCircle -ws

Add ``-o`` to open the saved result. By default, both videos and images
are written to ``videos/`` relative to the working directory.
See :doc:`configuration` for output and rendering options.

Interactive workflow
--------------------

Add ``self.embed()`` at the end of ``construct`` to enter an IPython
session after the animation. You can then modify objects and play more
animations, for example:

.. code-block:: python

    play(circle.animate.shift(2 * RIGHT))

Running ``manimgl`` without a scene file starts an interactive session directly.

More examples
-------------

Use the repository's ``example_scenes.py`` for examples of text, graphs,
updaters, and surfaces. Run a scene by its class name:

.. code-block:: sh

    manimgl example_scenes.py OpeningManimExample

The source file contains the examples and their explanatory comments together,
so it reflects the code in your checkout.
