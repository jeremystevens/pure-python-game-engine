"""Path-aware, cached image asset loading using tkinter."""

from pathlib import Path
import tkinter as tk
from typing import Callable, Dict, Iterable, Optional, Union


PathLike = Union[str, Path]
ImageFactory = Callable[..., object]


class AssetError(Exception):
    """Base error raised by the asset system."""


class AssetNotFoundError(AssetError, FileNotFoundError):
    """Raised when an asset path does not identify a file."""


class UnsupportedAssetError(AssetError, ValueError):
    """Raised when an asset format is not supported."""


class AssetLoadError(AssetError):
    """Raised when tkinter cannot decode an otherwise supported image."""


class AssetManager:
    """Resolve and cache Tk-compatible image assets by canonical path."""

    SUPPORTED_IMAGE_EXTENSIONS = frozenset({'.png', '.gif', '.pgm', '.ppm'})

    def __init__(
        self,
        asset_root: Optional[PathLike] = None,
        image_factory: Optional[ImageFactory] = None,
    ):
        root = Path.cwd() if asset_root is None else Path(asset_root)
        self.asset_root = root.expanduser().resolve()
        self._image_factory = image_factory or tk.PhotoImage
        self._images: Dict[Path, object] = {}

    @property
    def image_count(self) -> int:
        """Return the number of images currently retained in the cache."""
        return len(self._images)

    def resolve(self, path: PathLike) -> Path:
        """Resolve an asset path against the configured root."""
        candidate = Path(path).expanduser()
        if not candidate.is_absolute():
            candidate = self.asset_root / candidate
        return candidate.resolve()

    def load_image(self, path: PathLike, reload: bool = False):
        """Load and cache an image, or return its existing cached instance."""
        resolved = self.resolve(path)
        self._validate_image_path(resolved)

        if not reload and resolved in self._images:
            return self._images[resolved]

        try:
            image = self._image_factory(file=str(resolved))
        except (OSError, RuntimeError, tk.TclError) as error:
            raise AssetLoadError(
                f"Could not load image asset '{resolved}': {error}"
            ) from error

        self._images[resolved] = image
        return image

    def get_image(self, path: PathLike):
        """Return a cached image without loading it, or ``None`` if absent."""
        return self._images.get(self.resolve(path))

    def is_image_loaded(self, path: PathLike) -> bool:
        """Return whether an image is present in the cache."""
        return self.resolve(path) in self._images

    def unload(self, path: PathLike) -> bool:
        """Remove an image from the cache, returning whether it was present."""
        resolved = self.resolve(path)
        if resolved not in self._images:
            return False
        del self._images[resolved]
        return True

    def clear(self):
        """Release all cached image references."""
        self._images.clear()

    def loaded_image_paths(self) -> Iterable[Path]:
        """Return an immutable snapshot of cached image paths."""
        return tuple(self._images)

    def _validate_image_path(self, path: Path):
        if not path.is_file():
            raise AssetNotFoundError(f"Image asset not found: '{path}'")
        if path.suffix.lower() not in self.SUPPORTED_IMAGE_EXTENSIONS:
            supported = ', '.join(sorted(self.SUPPORTED_IMAGE_EXTENSIONS))
            raise UnsupportedAssetError(
                f"Unsupported image format '{path.suffix or '<none>'}' for "
                f"'{path}'. Supported formats: {supported}"
            )
