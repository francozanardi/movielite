import cv2
import numpy as np
import numba
from abc import abstractmethod
from typing import Callable, Union, Tuple, Optional, TYPE_CHECKING
import inspect
from .media_clip import MediaClip

try:
    from typing import Self # type: ignore[attr-defined]
except ImportError:
    from typing_extensions import Self

if TYPE_CHECKING:
    from ..vfx.base import GraphicEffect
    from ..vtx.base import Transition

class GraphicClip(MediaClip):
    """
    Base class for all visual/graphic clips (video, image, text, etc).

    A GraphicClip has visual properties (position, opacity, scale, size) and can be rendered.
    """

    def __init__(self, start: float, duration: float):
        """
        Initialize a GraphicClip.

        Args:
            start: Start time in seconds
            duration: Duration in seconds
        """
        super().__init__(start, duration)
        self._size: Tuple[int, int] = (0, 0)
        self._target_size: Optional[Tuple[int, int]] = None
        self._position: Callable[[float], Tuple[int, int]] = lambda t: (0, 0)
        self._opacity: Callable[[float], float] = lambda t: 1
        self._scale: Callable[[float], float] = lambda t: 1
        self._frame_transforms: list[Callable[[np.ndarray, float], np.ndarray]] = []
        self._has_any_transform = False
        self._mask: Optional['GraphicClip'] = None

    def set_position(self, value: Union[Callable[[float], Tuple[int, int]], Tuple[int, int]]) -> Self:
        """
        Set the position of the clip.

        Args:
            value: Either a tuple (x, y) or a function that takes time and returns (x, y)

        Returns:
            Self for chaining
        """
        self._position = self._save_as_function(value)
        self._has_any_transform = True
        return self

    def set_opacity(self, value: Union[Callable[[float], float], float]) -> Self:
        """
        Set the opacity of the clip.

        Args:
            value: Either a float (0-1) or a function that takes time and returns opacity

        Returns:
            Self for chaining
        """
        self._opacity = self._save_as_function(value)
        self._has_any_transform = True
        return self

    def set_scale(self, value: Union[Callable[[float], float], float]) -> Self:
        """
        Set the scale of the clip.

        Args:
            value: Either a float or a function that takes time and returns scale

        Returns:
            Self for chaining
        """
        self._scale = self._save_as_function(value)
        self._has_any_transform = True
        return self

    def set_size(self, width: Optional[int] = None, height: Optional[int] = None) -> Self:
        """
        Set the size of the clip, maintaining aspect ratio if only one dimension is provided.

        The resize is applied lazily (only when needed during rendering).

        Args:
            width: Target width (optional)
            height: Target height (optional)

        Returns:
            Self for chaining
        """
        if width is None and height is None:
            raise ValueError(f"Either width ({width}) or height ({height}) must contain a value")

        if width is None:
            if height <= 0:
                raise ValueError(f"Invalid combination of widthxheight: {width}x{height}")
            new_w = int((height / self._size[1]) * self._size[0])
            new_h = int(height)
        elif height is None:
            if width <= 0:
                raise ValueError(f"Invalid combination of widthxheight: {width}x{height}")
            new_w = int(width)
            new_h = int((width / self._size[0]) * self._size[1])
        else:
            if width <= 0 or height <= 0:
                raise ValueError(f"Invalid combination of widthxheight: {width}x{height}")
            new_w = int(width)
            new_h = int(height)

        self._target_size = (new_w, new_h)
        self._has_any_transform = True
        return self
    
    def set_mask(self, mask: 'GraphicClip') -> Self:
        """
        Set a mask for this clip. The mask determines which pixels are visible.

        Args:
            mask: A GraphicClip to use as mask, or None to remove mask

        Returns:
            Self for chaining

        Example:
            >>> image = ImageClip("photo.png")
            >>> mask = ImageClip("mask.png")
            >>> image.set_mask(mask)
        """
        self._mask = mask
        self._has_any_transform = True
        return self

    def add_transform(self, callback: Callable[[np.ndarray, float], np.ndarray]) -> Self:
        """
        Apply a custom transformation to each frame at render time.
        Multiple transformations can be chained by calling this method multiple times.
        They will be applied in the order they were added.

        The callback receives the frame (np.ndarray) and relative time (float),
        and should return the transformed frame.

        IMPORTANT:
         The frame received and returned must be in BGR or BGRA format and uint8 type.
         The callback doesn't receive a copy of the frame, so modifications must be done carefully.

        Args:
            callback: Function that takes (frame, time) and returns transformed frame

        Returns:
            Self for chaining

        Example:
            >>> def make_sepia(frame, t):
            >>>     # Apply sepia filter
            >>>     return sepia_filter(frame)
            >>> def add_vignette(frame, t):
            >>>     # Apply vignette effect
            >>>     return vignette_filter(frame)
            >>> clip.add_transform(make_sepia).add_transform(add_vignette)
        """
        self._frame_transforms.append(callback)
        self._has_any_transform = True
        return self

    def add_effect(self, effect: 'GraphicEffect') -> Self:
        """
        Apply a visual effect to this clip.

        Args:
            effect: A GraphicEffect instance to apply

        Returns:
            Self for chaining

        Example:
            >>> from movielite import vfx
            >>> clip.add_effect(vfx.FadeIn(2.0)).add_effect(vfx.FadeOut(1.5))
        """
        effect.apply(self)
        return self

    def add_transition(self, other_clip: 'GraphicClip', transition: 'Transition') -> Self:
        """
        Apply a transition effect between this clip and another clip.

        Args:
            other_clip: The other GraphicClip to transition to/from
            transition: A Transition instance to apply

        Returns:
            Self for chaining

        Example:
            >>> from movielite import vtx
            >>> clip1.add_transition(clip2, vtx.CrossFade(0.5))
        """
        transition.apply(self, other_clip)
        return self

    def _save_as_function(self, value: Union[Callable, float, Tuple[int, int]]) -> Callable:
        """Convert static values to time-based functions"""
        if inspect.isfunction(value):
            return value
        return lambda t, v=value: v

    @property
    def position(self):
        return self._position

    @property
    def opacity(self):
        return self._opacity

    @property
    def scale(self):
        return self._scale

    @property
    def size(self):
        return self._target_size if self._target_size is not None else self._size
    
    @property
    def has_any_transform(self):
        return self._has_any_transform
    
    def close(self):
        """Closes the graphic clip and releases any resources"""
        pass

    def __del__(self):
        """Ensure the graphic clip is closed when object is destroyed"""
        self.close()

    @abstractmethod
    def get_frame(self, t_rel: float) -> np.ndarray:
        """
        Get the frame at a relative time within the clip.
        The returned frame does not include any transformations (position, scale, size, opacity, custom transforms).

        IMPORTANT: the frame returned must be BGR or BGRA format and uint8 type.

        Args:
            t_rel: Relative time within the clip (0 to duration)

        Returns:
            Frame as numpy array (BGRA, uint8)
        """
        pass

    @abstractmethod
    def _apply_resize(self, frame: np.ndarray) -> np.ndarray:
        """
        Apply resize transformation to a frame.

        Args:
            frame: The frame to resize

        Returns:
            Resized frame
        """
        pass

    @abstractmethod
    def _convert_to_mask(self, frame: np.ndarray) -> np.ndarray:
        """
        Convert a BGR/BGRA frame to a 2D mask array.

        Args:
            frame: BGR or BGRA frame (uint8)

        Returns:
            2D uint8 array with values between 0 (transparent) and 255 (opaque)
        """
        pass

    def _apply_transforms(self, frame: np.ndarray, t_rel: float) -> np.ndarray:
        """
        Apply size, scale, and custom transforms to a frame.

        Args:
            frame: Input frame (BGR/BGRA uint8)
            t_rel: Relative time

        Returns:
            Transformed frame
        """
        if self._target_size is not None:
            frame = self._apply_resize(frame)

        for transform in self._frame_transforms:
            frame = transform(frame, t_rel)

        s = self.scale(t_rel)
        # There's a possible optimization here:
        # If the clip is an image and the scale is constant, we could cache the scaled image.
        if s != 1.0:
            # source: https://docs.opencv.org/3.4/da/d54/group__imgproc__transform.html#ga47a974309e9102f5f08231edc7e7529d
            # "To shrink an image, it will generally look best with INTER_AREA interpolation, whereas to enlarge an image,
            #  it will generally look best with INTER_CUBIC (slow) or INTER_LINEAR (faster but still looks OK)."
            interpolation_method = cv2.INTER_AREA if s < 1.0 else cv2.INTER_CUBIC
            new_w = int(frame.shape[1] * s)
            new_h = int(frame.shape[0] * s)
            frame = cv2.resize(frame, (new_w, new_h), interpolation=interpolation_method)
            frame = np.clip(frame, 0.0, 255.0)

        return frame

    def render(self, bg: np.ndarray, t_global: float) -> np.ndarray:
        """
        Render this clip onto a background at a given global time.

        IMPORTANT: It modifies the background (bg) in-place.

        Args:
            bg: Background frame (BGR format), assumes float32 type
            t_global: Global time in seconds

        Returns:
            Background with this clip rendered on top
        """
        t_rel = (t_global - self._start)

        if not (0 <= t_rel < self._duration):
            return bg

        frame = self.get_frame(t_rel)
        frame = self._apply_transforms(frame, t_rel)

        mask = None
        mask_x, mask_y = 0, 0
        mask_opacity_multiplier = 1.0
        if self._mask is not None:
            # There's a small possible improvement here:
            #  When the mask clip is an image, we're doing the convertion from BGR/BGRA to mask every frame render.
            #  We could do the conversion once and cache it.
            # However, this would require do the transformations over the mask, which may result in a specific and more complex logic.
            mask = self._mask.get_frame(t_rel)
            mask = self._mask._apply_transforms(mask, t_rel)
            mask = self._convert_to_mask(mask)
            mask_x, mask_y = self._mask.position(t_rel)
            mask_x, mask_y = int(mask_x), int(mask_y)
            mask_opacity_multiplier = self._mask.opacity(t_rel)

        x, y = self.position(t_rel)
        x, y = int(x), int(y)
        alpha_multiplier = self.opacity(t_rel)

        H, W = bg.shape[:2]
        h, w = frame.shape[:2]

        y1_bg = max(y, 0)
        x1_bg = max(x, 0)
        y2_bg = min(y + h, H)
        x2_bg = min(x + w, W)

        if y1_bg >= y2_bg or x1_bg >= x2_bg:
            return bg

        # Frame coordinates
        y1_fr = y1_bg - y
        x1_fr = x1_bg - x
        y2_fr = y2_bg - y
        x2_fr = x2_bg - x

        roi = bg[y1_bg:y2_bg, x1_bg:x2_bg]
        sub_fr = frame[y1_fr:y2_fr, x1_fr:x2_fr]

        if bg.shape[2] == 3:
            blend_foreground_with_bgr_background_inplace(roi, sub_fr, x, y, alpha_multiplier, mask, mask_x, mask_y, mask_opacity_multiplier)
        else:
            blend_foreground_with_bgra_background_inplace(roi, sub_fr, x, y, alpha_multiplier, mask, mask_x, mask_y, mask_opacity_multiplier)

        return bg

@numba.jit(nopython=True, cache=True)
def blend_foreground_with_bgr_background_inplace(
    background_bgr,
    foreground_uint8,
    fg_x,
    fg_y,
    fg_opacitiy_multiplier,
    mask,
    mask_x,
    mask_y,
    mask_opacity_multiplier
):
    """
    Blends foreground (BGRA or BGR, type uint8) over background (BGR, type float32).
    Modifies background_bgr in-place.

    Args:
        background_bgr: Background ROI (BGR, float32)
        foreground_uint8: Foreground sub-frame (BGR/BGRA, uint8)
        fg_x, fg_y: Foreground position in absolute coordinates
        fg_opacitiy_multiplier: Opacity value for foreground (0-1)
        mask: Optional 2D mask array (uint8, 0-255), or None
        mask_x, mask_y: Mask position in absolute coordinates
        mask_opacity_multiplier: Opacity multiplier for mask values (0-1)
    """
    for y in range(foreground_uint8.shape[0]):
        for x in range(foreground_uint8.shape[1]):
            fg_b_uint = foreground_uint8[y, x, 0]
            fg_g_uint = foreground_uint8[y, x, 1]
            fg_r_uint = foreground_uint8[y, x, 2]

            fg_b = float(fg_b_uint)
            fg_g = float(fg_g_uint)
            fg_r = float(fg_r_uint)
            fg_a = (float(foreground_uint8[y, x, 3]) / 255.0) * fg_opacitiy_multiplier if foreground_uint8.shape[2] == 4 else fg_opacitiy_multiplier

            if mask is not None:
                abs_y = fg_y + y
                abs_x = fg_x + x
                mask_rel_y = abs_y - mask_y
                mask_rel_x = abs_x - mask_x

                if 0 <= mask_rel_y < mask.shape[0] and 0 <= mask_rel_x < mask.shape[1]:
                    mask_value = (float(mask[mask_rel_y, mask_rel_x]) / 255.0) * mask_opacity_multiplier
                else:
                    mask_value = 0.0  # Outside mask = invisible

                fg_a *= mask_value

            if fg_a <= 0:
                continue

            if fg_a >= 1:
                background_bgr[y, x, 0] = fg_b
                background_bgr[y, x, 1] = fg_g
                background_bgr[y, x, 2] = fg_r
                continue

            inv_a = 1.0 - fg_a

            out_b = fg_b * fg_a + background_bgr[y, x, 0] * inv_a
            background_bgr[y, x, 0] = min(255.0, max(0.0, out_b))

            out_g = fg_g * fg_a + background_bgr[y, x, 1] * inv_a
            background_bgr[y, x, 1] = min(255.0, max(0.0, out_g))

            out_r = fg_r * fg_a + background_bgr[y, x, 2] * inv_a
            background_bgr[y, x, 2] = min(255.0, max(0.0, out_r))

@numba.jit(nopython=True, cache=True)
def blend_foreground_with_bgra_background_inplace(
    background_bgra,
    foreground_uint8,
    fg_x,
    fg_y,
    fg_opacitiy_multiplier,
    mask,
    mask_x,
    mask_y,
    mask_opacity_multiplier
):
    """
    Blends foreground (BGRA or BGR, type uint8) over background (BGRA, type float32).
    Modifies background_bgra in-place.

    Args:
        background_bgra: Background ROI (BGRA, float32)
        foreground_uint8: Foreground sub-frame (BGR/BGRA, uint8)
        fg_x, fg_y: Foreground position in absolute coordinates
        fg_opacitiy_multiplier: Opacity value for foreground (0-1)
        mask: Optional 2D mask array (uint8, 0-255), or None
        mask_x, mask_y: Mask position in absolute coordinates
        mask_opacity_multiplier: Opacity multiplier for mask values (0-1)
    """
    for y in range(foreground_uint8.shape[0]):
        for x in range(foreground_uint8.shape[1]):
            fg_b_uint = foreground_uint8[y, x, 0]
            fg_g_uint = foreground_uint8[y, x, 1]
            fg_r_uint = foreground_uint8[y, x, 2]

            fg_b = float(fg_b_uint)
            fg_g = float(fg_g_uint)
            fg_r = float(fg_r_uint)
            fg_a = (float(foreground_uint8[y, x, 3]) / 255.0) * fg_opacitiy_multiplier if foreground_uint8.shape[2] == 4 else fg_opacitiy_multiplier

            if mask is not None:
                abs_y = fg_y + y
                abs_x = fg_x + x
                mask_rel_y = abs_y - mask_y
                mask_rel_x = abs_x - mask_x

                if 0 <= mask_rel_y < mask.shape[0] and 0 <= mask_rel_x < mask.shape[1]:
                    mask_value = (float(mask[mask_rel_y, mask_rel_x]) / 255.0) * mask_opacity_multiplier
                else:
                    mask_value = 0.0  # Outside mask = invisible

                fg_a *= mask_value

            if fg_a <= 0:
                continue

            if fg_a >= 1.0:
                background_bgra[y, x, 0] = fg_b
                background_bgra[y, x, 1] = fg_g
                background_bgra[y, x, 2] = fg_r
                background_bgra[y, x, 3] = 255.0
                continue

            bg_a = background_bgra[y, x, 3] / 255.0

            out_a = fg_a + bg_a * (1.0 - fg_a)

            if out_a < 1e-6:
                background_bgra[y, x, 0] = 0.0
                background_bgra[y, x, 1] = 0.0
                background_bgra[y, x, 2] = 0.0
                background_bgra[y, x, 3] = 0.0
                continue

            bg_r, bg_g, bg_b = background_bgra[y, x, 2], background_bgra[y, x, 1], background_bgra[y, x, 0]

            out_r = (fg_r * fg_a + bg_r * bg_a * (1.0 - fg_a)) / out_a
            out_g = (fg_g * fg_a + bg_g * bg_a * (1.0 - fg_a)) / out_a
            out_b = (fg_b * fg_a + bg_b * bg_a * (1.0 - fg_a)) / out_a

            background_bgra[y, x, 2] = min(255.0, max(0.0, out_r))
            background_bgra[y, x, 1] = min(255.0, max(0.0, out_g))
            background_bgra[y, x, 0] = min(255.0, max(0.0, out_b))
            background_bgra[y, x, 3] = out_a * 255.0
