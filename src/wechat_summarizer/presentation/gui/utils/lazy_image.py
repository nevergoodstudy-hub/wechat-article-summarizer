"""Lazy-loaded image widget."""

from __future__ import annotations

import logging
import threading
import tkinter as tk
from typing import Any, cast

logger = logging.getLogger(__name__)


class LazyImage(tk.Label):
    """Label that loads and resizes an image in a background thread."""

    def __init__(
        self,
        parent: tk.Misc,
        image_path: str | None = None,
        placeholder_text: str = "\U0001f5bc",
        width: int = 100,
        height: int = 100,
        **kwargs: Any,
    ) -> None:
        bg = kwargs.pop("bg", "#1a1a1a")
        super().__init__(
            parent,
            text=placeholder_text,
            bg=bg,
            fg="#404040",
            font=("Segoe UI", 24),
            width=width // 10,
            height=height // 20,
            **kwargs,
        )

        self._image_path = image_path
        self._width = width
        self._height = height
        self._photo_image: Any | None = None

        if image_path:
            self._load_image()

    def _load_image(self) -> None:
        """Load the configured image asynchronously."""
        image_path = self._image_path
        if not image_path:
            return

        def _load() -> None:
            try:
                from PIL import Image

                source_image = Image.open(image_path)
                resized_image = source_image.resize(
                    (self._width, self._height),
                    Image.Resampling.LANCZOS,
                )
                self.after(0, lambda: self._set_image(resized_image))

            except Exception as exc:
                logger.error("图片加载失败: %s", exc)

        thread = threading.Thread(target=_load, daemon=True)
        thread.start()

    def _set_image(self, img: Any) -> None:
        """Apply a loaded PIL image to the Tk label."""
        try:
            from PIL import ImageTk

            self._photo_image = ImageTk.PhotoImage(img)
            self.configure(image=cast(str, self._photo_image), text="")
        except Exception as exc:
            logger.error("图片设置失败: %s", exc)

    def set_image_path(self, path: str) -> None:
        """Set a new path and start image loading."""
        self._image_path = path
        self._load_image()


__all__ = ["LazyImage"]
