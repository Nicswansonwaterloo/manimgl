import unittest

import numpy as np

from manimlib import DotCloud, FadeIn, FadeOut, Group, Line3D, linear
from manimlib.camera.camera import Camera


class CoincidentDepthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.camera = Camera(resolution=(320, 180), background_color="#ffffff")
        except RuntimeError as error:
            raise unittest.SkipTest(f"GPU unavailable: {error}") from error

    def objects(self, color):
        return Group(
            DotCloud(np.array([[x, 1.7, 0] for x in range(-2, 3)]),
                     radius=0.20, color=color, depth_test=True),
            Line3D(np.array([-2.5, 0, 0]), np.array([2.5, 0, 0]),
                   width=0.25, resolution=(25, 2), color=color,
                   shading=(0, 0, 0), depth_test=True),
            DotCloud(np.array([[x, -1.7, 0] for x in range(-2, 3)]),
                     radius=0.20, color=color, depth_test=False),
        )

    def pixel(self, y=0):
        camera = self.camera
        row = int(camera.get_pixel_height() * (0.5 - y / camera.get_frame_height()))
        return np.array(camera.get_image())[row, camera.get_pixel_width() // 2, :3].astype(int)

    def test_crossfade_shows_incoming_dots_and_cylinder_before_removal(self):
        camera = self.camera
        for samples in (1, 4):
            camera.samples = samples
            camera.init_target()
            outgoing, incoming = self.objects("#c91b38"), self.objects("#0054c7")
            fades = FadeOut(outgoing, rate_func=linear), FadeIn(incoming, rate_func=linear)
            for fade in fades:
                fade.begin()
            for alpha in (0, 0.25, 0.5, 0.75, 1):
                with self.subTest(samples=samples, alpha=alpha):
                    for fade in fades:
                        fade.interpolate(alpha)
                    camera.capture(outgoing)
                    red_only = self.pixel()
                    # Repeat frames to exercise both direct draws and cached bundles.
                    for _ in range(4):
                        camera.capture(outgoing, incoming)
                    np.testing.assert_array_equal(self.pixel(1.7), self.pixel(-1.7))
                    expected = (
                        alpha * np.array([0, 84, 199])
                        + (1 - alpha) ** 2 * np.array([201, 27, 56])
                        + alpha * (1 - alpha) * 255
                    )
                    np.testing.assert_allclose(self.pixel(1.7), expected, atol=2)
                    if alpha > 0:
                        blended = self.pixel()
                        self.assertGreater(blended[2] - blended[0], red_only[2] - red_only[0])
            before_removal = np.array(camera.get_image())
            for fade in fades:
                fade.finish()
            camera.capture(incoming)
            np.testing.assert_array_equal(np.array(camera.get_image()), before_removal)

    def test_nearer_opaque_geometry_still_occludes_farther_geometry(self):
        camera = self.camera
        for factory in (
            lambda color: DotCloud(np.array([[0., 0., 0.]]), radius=0.4,
                                   color=color, depth_test=True),
            lambda color: Line3D(np.array([-2., 0., 0.]), np.array([2., 0., 0.]),
                                 width=0.5, color=color, shading=(0, 0, 0)),
        ):
            near, far = factory("#c91b38").shift([0, 0, 1]), factory("#0054c7")
            camera.capture(near)
            expected = self.pixel()
            for order in ((near, far), (far, near)):
                with self.subTest(factory=factory, order=order):
                    camera.capture(*order)
                    np.testing.assert_array_equal(self.pixel(), expected)


if __name__ == "__main__":
    unittest.main()
