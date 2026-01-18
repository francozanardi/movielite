import cv2
import numpy as np
from typing import Callable, Union, Optional, Tuple
from ..core import GraphicClip
from .base import GraphicEffect


class Rotation(GraphicEffect):
    """
    Rotation effect that rotates the clip by a specified angle.
    Supports both static and animated (time-based) rotation.
    """

    def __init__(
        self,
        angle: Union[Callable[[float], float], float],
        unit: str = "deg",
        resample: str = "bilinear",
        expand: bool = True,
        center: Optional[Tuple[float, float]] = None,
        translate: Optional[Tuple[float, float]] = None,
        bg_color: Optional[Tuple[int, ...]] = None
    ):
        """
        Create a rotation effect.

        Args:
            angle: Rotation angle. Can be:
                   - A float for static rotation (e.g., 45)
                   - A function of time for animated rotation (e.g., lambda t: t * 360)
                   Positive values rotate counter-clockwise.
            unit: Unit of the angle, either "deg" (degrees) or "rad" (radians).
                  Default is "deg".
            resample: Resampling filter. One of:
                      - "nearest": Fastest, but can look blocky
                      - "bilinear": Good balance of speed and quality (default)
                      - "bicubic": Best quality, but slower
            expand: If True (default), expands the canvas to fit the rotated content
                    without clipping corners. If False, keeps original size (may clip).
            center: Center of rotation as (x, y). If None (default), uses the center
                    of the frame. Values are in pixels relative to top-left corner.
            translate: Optional post-rotation translation as (dx, dy) in pixels.
            bg_color: Background color for areas outside the rotated frame.
                      For RGB: (R, G, B). For RGBA: (R, G, B, A).
                      If None (default), uses black or transparent based on frame type.

        Example:
            >>> from movielite import vfx
            >>> clip.add_effect(vfx.Rotation(45))  # Static 45-degree rotation
            >>> clip.add_effect(vfx.Rotation(lambda t: t * 360))  # Full rotation per second
            >>> clip.add_effect(vfx.Rotation(90, resample="bicubic"))  # High quality
        """
        self.angle = angle if callable(angle) else lambda t: angle
        self.unit = unit
        self.expand = expand
        self.center = center
        self.translate = translate
        self.bg_color = bg_color

        resample_map = {
            "nearest": cv2.INTER_NEAREST,
            "bilinear": cv2.INTER_LINEAR,
            "bicubic": cv2.INTER_CUBIC,
        }
        if resample not in resample_map:
            raise ValueError(
                f"'resample' must be one of {list(resample_map.keys())}, got '{resample}'"
            )
        self.resample = resample_map[resample]

    def apply(self, clip: GraphicClip) -> None:
        """Apply rotation effect by adding a frame transform."""

        def rotation_transform(frame: np.ndarray, t: float) -> np.ndarray:
            angle = self.angle(t)
            if self.unit == "rad":
                angle = np.degrees(angle)

            # Normalize angle to 0-360 range
            angle = angle % 360

            # Optimization: for common angles without special params, use fast numpy operations
            if self.center is None and self.translate is None and self.bg_color is None:
                if angle == 0 and self.expand:
                    return frame
                if angle == 90 and self.expand:
                    # Rotate 90° CCW: transpose then flip vertically
                    return np.rot90(frame, k=1)
                if angle == 180 and self.expand:
                    # Rotate 180°: flip both axes
                    return frame[::-1, ::-1]
                if angle == 270 and self.expand:
                    # Rotate 270° CCW (= 90° CW): transpose then flip horizontally
                    return np.rot90(frame, k=3)

            if angle == 0 and not self.translate:
                return frame

            return _rotate_frame(
                frame,
                angle,
                self.resample,
                self.expand,
                self.center,
                self.translate,
                self.bg_color
            )

        clip.add_transform(rotation_transform)


def _rotate_frame(
    frame: np.ndarray,
    angle: float,
    resample: int,
    expand: bool,
    center: Optional[Tuple[float, float]],
    translate: Optional[Tuple[float, float]],
    bg_color: Optional[Tuple[int, ...]]
) -> np.ndarray:
    """
    Apply rotation to a frame using OpenCV's warpAffine.

    Args:
        frame: Input frame (BGR/BGRA uint8)
        angle: Rotation angle in degrees (counter-clockwise)
        resample: OpenCV interpolation flag
        expand: Whether to expand the canvas to fit rotated content
        center: Center of rotation, or None for frame center
        translate: Post-rotation translation, or None
        bg_color: Background color, or None for auto

    Returns:
        Rotated frame
    """
    h, w = frame.shape[:2]
    has_alpha = len(frame.shape) == 3 and frame.shape[2] == 4

    # Determine background color
    if bg_color is None:
        if has_alpha:
            border_value = (0, 0, 0, 0)
        else:
            border_value = (0, 0, 0)
    else:
        border_value = bg_color

    # Determine rotation center
    if center is not None:
        cx, cy = center
    else:
        cx, cy = w / 2, h / 2

    rotation_matrix = cv2.getRotationMatrix2D((cx, cy), angle, 1.0)

    if expand:
        # Calculate new bounding box size to fit the rotated image
        cos_a = abs(rotation_matrix[0, 0])
        sin_a = abs(rotation_matrix[0, 1])
        new_w = int(np.ceil(h * sin_a + w * cos_a))
        new_h = int(np.ceil(h * cos_a + w * sin_a))

        # Adjust rotation matrix to account for translation to new center
        rotation_matrix[0, 2] += (new_w / 2) - cx
        rotation_matrix[1, 2] += (new_h / 2) - cy
    else:
        new_w, new_h = w, h

    rotated = cv2.warpAffine(
        frame,
        rotation_matrix,
        (new_w, new_h),
        flags=resample,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=border_value
    )

    # Apply post-rotation translation if specified
    if translate is not None:
        translation_matrix = np.float32([
            [1, 0, translate[0]],
            [0, 1, translate[1]]
        ])
        rotated = cv2.warpAffine(
            rotated,
            translation_matrix,
            (rotated.shape[1], rotated.shape[0]),
            flags=resample,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=border_value
        )

    return rotated
