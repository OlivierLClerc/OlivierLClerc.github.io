import unittest

import numpy as np

from scripts.build_gallery_metadata import determine_photo_mode
from scripts.prepare_gallery_photos import detect_photo_frame_depths, measure_frame_pixels


class GalleryPreprocessingTests(unittest.TestCase):
    def test_wider_opposite_borders_use_square_crop(self):
        pixels = np.full((256, 256, 3), 255, dtype=np.uint8)
        pixels[8:248, 16:240] = 40
        depths = measure_frame_pixels(pixels)
        self.assertEqual(detect_photo_frame_depths(depths, shared_border=8), 16)

    def test_white_scene_does_not_trigger_oversized_crop(self):
        pixels = np.full((256, 256, 3), 255, dtype=np.uint8)
        pixels[90:166, 90:166] = 40
        depths = measure_frame_pixels(pixels)
        self.assertEqual(detect_photo_frame_depths(depths, shared_border=8), 8)
        self.assertEqual(detect_photo_frame_depths((178, 162, 196, None), shared_border=51), 51)

    def test_wider_top_and_bottom_borders(self):
        self.assertEqual(detect_photo_frame_depths((77, 76, 51, 51), shared_border=51), 77)

    def test_small_color_highlight_is_not_monochrome(self):
        rgb = np.zeros((256, 256, 3), dtype=np.float32)
        rgb[120:132, 120:132, 0] = 0.8
        rgb[120:132, 120:132, 1] = 0.2
        value = rgb.max(axis=2)
        spread = value - rgb.min(axis=2)
        saturation = np.divide(spread, value + 1e-6)
        self.assertEqual(determine_photo_mode(saturation, spread, value), "color")

    def test_grayscale_stays_monochrome(self):
        values = np.linspace(0, 1, 256, dtype=np.float32)
        rgb = np.broadcast_to(values[:, None, None], (256, 256, 3))
        value = rgb.max(axis=2)
        spread = value - rgb.min(axis=2)
        saturation = np.divide(spread, value + 1e-6)
        self.assertEqual(determine_photo_mode(saturation, spread, value), "bw")


if __name__ == "__main__":
    unittest.main()
