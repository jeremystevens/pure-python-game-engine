import tempfile
import tkinter as tk
import unittest
from pathlib import Path

from engine.assets import (
    AssetLoadError,
    AssetManager,
    AssetNotFoundError,
    UnsupportedAssetError,
)


class RecordingImageFactory:
    def __init__(self):
        self.calls = []

    def __call__(self, **kwargs):
        image = object()
        self.calls.append((kwargs, image))
        return image


class AssetManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_directory.cleanup)
        self.root = Path(self.temp_directory.name)
        self.images = self.root / 'images'
        self.images.mkdir()
        self.factory = RecordingImageFactory()
        self.assets = AssetManager(self.root, self.factory)

    def create_asset(self, relative_path, contents=b'image data'):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)
        return path

    def test_relative_and_absolute_paths_resolve_canonically(self):
        path = self.create_asset('images/player.png')

        self.assertEqual(self.assets.resolve('images/player.png'), path.resolve())
        self.assertEqual(self.assets.resolve(path), path.resolve())
        self.assertEqual(
            self.assets.resolve('images/../images/player.png'),
            path.resolve(),
        )

    def test_load_image_caches_by_resolved_path(self):
        path = self.create_asset('images/player.png')

        first = self.assets.load_image('images/player.png')
        second = self.assets.load_image(path)
        alias = self.assets.load_image('images/../images/player.png')

        self.assertIs(first, second)
        self.assertIs(first, alias)
        self.assertEqual(len(self.factory.calls), 1)
        self.assertEqual(
            self.factory.calls[0][0],
            {'file': str(path.resolve())},
        )
        self.assertEqual(self.assets.image_count, 1)
        self.assertTrue(self.assets.is_image_loaded(path))
        self.assertIs(self.assets.get_image(path), first)

    def test_reload_replaces_cached_image(self):
        path = self.create_asset('images/player.gif')
        first = self.assets.load_image(path)

        second = self.assets.load_image(path, reload=True)

        self.assertIsNot(first, second)
        self.assertIs(self.assets.get_image(path), second)
        self.assertEqual(len(self.factory.calls), 2)
        self.assertEqual(self.assets.image_count, 1)

    def test_unload_and_clear_release_cached_references(self):
        first_path = self.create_asset('images/first.ppm')
        second_path = self.create_asset('images/second.pgm')
        self.assets.load_image(first_path)
        self.assets.load_image(second_path)

        self.assertEqual(
            set(self.assets.loaded_image_paths()),
            {first_path.resolve(), second_path.resolve()},
        )
        self.assertTrue(self.assets.unload(first_path))
        self.assertFalse(self.assets.unload(first_path))
        self.assertIsNone(self.assets.get_image(first_path))

        self.assets.clear()
        self.assertEqual(self.assets.image_count, 0)
        self.assertEqual(tuple(self.assets.loaded_image_paths()), ())

    def test_missing_file_raises_clear_error(self):
        with self.assertRaisesRegex(AssetNotFoundError, 'Image asset not found'):
            self.assets.load_image('images/missing.png')

    def test_directory_is_not_accepted_as_an_image(self):
        with self.assertRaises(AssetNotFoundError):
            self.assets.load_image('images')

    def test_unsupported_or_extensionless_file_is_rejected(self):
        self.create_asset('images/photo.jpg')
        self.create_asset('images/no_extension')

        with self.assertRaisesRegex(UnsupportedAssetError, r'\.jpg'):
            self.assets.load_image('images/photo.jpg')
        with self.assertRaisesRegex(UnsupportedAssetError, '<none>'):
            self.assets.load_image('images/no_extension')

    def test_supported_extensions_are_case_insensitive(self):
        path = self.create_asset('images/player.PNG')

        image = self.assets.load_image(path)

        self.assertIs(image, self.factory.calls[0][1])

    def test_tk_decode_errors_are_wrapped_with_asset_context(self):
        path = self.create_asset('images/broken.png')

        def failing_factory(**kwargs):
            raise tk.TclError('invalid image data')

        assets = AssetManager(self.root, failing_factory)
        with self.assertRaisesRegex(AssetLoadError, str(path.resolve())) as context:
            assets.load_image(path)

        self.assertIsInstance(context.exception.__cause__, tk.TclError)
        self.assertEqual(assets.image_count, 0)

    def test_default_root_is_current_working_directory(self):
        assets = AssetManager(image_factory=self.factory)

        self.assertEqual(assets.asset_root, Path.cwd().resolve())


if __name__ == '__main__':
    unittest.main()
