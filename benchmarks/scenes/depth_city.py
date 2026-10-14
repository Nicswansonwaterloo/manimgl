from manimlib import *


class DepthCity500(ThreeDScene):
    """500 individual buildings (3,000 surface faces), depth occlusion and camera flight."""
    default_camera_config = dict(background_color="#B4D5E8", light_source_position=[-8, -6, 12])

    def construct(self):
        rng = np.random.default_rng(500)
        city = Group()
        palette = color_gradient([BLUE_E, GREY_B, GOLD_E, TEAL_E], 20)
        for row in range(20):
            for col in range(25):
                height = rng.uniform(0.2, 2.2)
                city.add(Prism(width=0.32, height=0.32, depth=height,
                               color=palette[(row + col) % 20], shading=(0.35, 0.5, 0.4))
                         .move_to([(col - 12) * 0.45, (row - 9.5) * 0.45, height / 2]))
        ground = Square3D(side_length=13, color="#294750").shift(0.02 * IN)
        self.frame.set_height(15).reorient(-35, 55)
        self.add(ground, city)
        self.play(self.frame.animate.reorient(25, 65).set_height(10).move_to([1, 0, 1]),
                  run_time=4, rate_func=linear)
