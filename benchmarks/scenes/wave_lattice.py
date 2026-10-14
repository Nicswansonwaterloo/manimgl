from manimlib import *


class WaveLattice500(Scene):
    """500 filled vector mobjects with independent wave-driven size, color and position."""
    default_camera_config = dict(background_color="#F3EFE4")

    def construct(self):
        tiles = VGroup()
        palette = color_gradient([BLUE_E, TEAL, GOLD_E, RED_E], 100)
        for row in range(20):
            for col in range(25):
                home = np.array([(col - 12) * 0.43, (row - 9.5) * 0.28, 0])
                tile = Square(0.2, stroke_width=0, fill_opacity=1)

                def update(m, dt, row=row, col=col, home=home):
                    phase = 3 * self.time + 0.28 * col + 0.4 * row
                    m.set_width(0.13 + 0.1 * (1 + np.sin(phase)))
                    m.move_to(home + 0.07 * np.cos(phase) * UP)
                    m.set_color(palette[int(49 * (1 + np.sin(phase)))])

                tile.add_updater(update)
                tiles.add(tile)
        label = Text("500 independent vector tiles", font="sans-serif", font_size=26, fill_color=BLACK).to_edge(UP)
        self.add(label, tiles)
        self.wait(4)
