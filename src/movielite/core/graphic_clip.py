import cv2
import numpy as np
import numba
from abc import abstractmethod
from typing import Callable, Union, Tuple, Optional, TYPE_CHECKING
import inspect
from .media_clip import MediaClip
from . import empty_frame

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
        self._pixel_transforms: list[Callable] = []  # numba-compiled pixel transforms
        self._frame_transforms: list[Callable[[np.ndarray, float], np.ndarray]] = []
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
        return self

    def set_rotation(
        self,
        angle: Union[Callable[[float], float], float],
        unit: str = "deg",
        resample: str = "bilinear",
        expand: bool = True,
        center: Optional[Tuple[float, float]] = None,
        translate: Optional[Tuple[float, float]] = None,
        bg_color: Optional[Tuple[int, ...]] = None
    ) -> Self:
        """
        Set the rotation of the clip.

        Args:
            angle: Rotation angle. Can be:
                   - A float for static rotation (e.g., 45)
                   - A function of time for animated rotation (e.g., lambda t: t * 360)
                   Positive values rotate counter-clockwise.
            unit: Unit of the angle, either "deg" (degrees) or "rad" (radians).
                  Default is "deg".
            resample: Resampling filter. One of "nearest", "bilinear" (default), 
                      or "bicubic".
            expand: If True (default), expands the canvas to fit the rotated content
                    without clipping corners. If False, keeps original size (may clip).
            center: Center of rotation as (x, y). If None (default), uses the center
                    of the frame. Values are in pixels relative to top-left corner.
            translate: Optional post-rotation translation as (dx, dy) in pixels.
            bg_color: Background color for areas outside the rotated frame.
                      If None (default), uses black or transparent based on frame type.

        Returns:
            Self for chaining

        Example:
            >>> clip.set_rotation(45)  # Static 45-degree rotation
            >>> clip.set_rotation(lambda t: t * 90)  # 90 degrees per second
            >>> clip.set_rotation(180, expand=False)  # Flip upside down, keep size
            >>> clip.set_rotation(math.pi / 2, unit="rad")  # 90 degrees in radians
        """
        from ..vfx.rotation import Rotation
        self.add_effect(Rotation(
            angle,
            unit=unit,
            resample=resample,
            expand=expand,
            center=center,
            translate=translate,
            bg_color=bg_color
        ))
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
        return self

    def add_pixel_transform(self, callback: Callable) -> Self:
        """
        Apply a per-pixel transformation at render time.
        Multiple pixel transformations can be chained and will be applied efficiently
        in a single pass using numba.

        The callback should be a numba-compiled function with signature:
            @numba.njit
            def transform(b: int, g: int, r: int, a: int, t: float) -> Tuple[int, int, int]

        All color values are uint8 (0-255), time is float.

        This is more efficient than add_transform for color adjustments because:
        - Multiple pixel transforms are batched into a single loop
        - Only one copy of the frame is made
        - All operations happen in-place with numba

        Args:
            callback: Numba-compiled function(b, g, r, a, t) -> (b, g, r)

        Returns:
            Self for chaining

        Example:
            >>> import numba
            >>> @numba.njit
            >>> def increase_brightness(b, g, r, a, t):
            >>>     factor = 1.2
            >>>     return (
            >>>         min(255, int(b * factor)),
            >>>         min(255, int(g * factor)),
            >>>         min(255, int(r * factor))
            >>>     )
            >>> clip.add_pixel_transform(increase_brightness)
        """
        self._pixel_transforms.append(callback)
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

    def add_transition(self, next_clip: 'GraphicClip', transition: 'Transition') -> Self:
        """
        Apply a transition effect between this clip and another clip.

        Args:
            next_clip: The other GraphicClip to transition to/from
            transition: A Transition instance to apply

        Returns:
            Self for chaining

        Example:
            >>> from movielite import vtx
            >>> clip1.add_transition(clip2, vtx.CrossFade(0.5))
        """
        transition.apply(self, next_clip)
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

        if self._pixel_transforms:
            frame = apply_batched_pixel_transforms(frame, self._pixel_transforms, t_rel)

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

        return frame
    
    def render_as_background(
            self,
            t_global: float,
            target_width: int,
            target_height: int,
            will_need_blending: bool,
            high_precision_blending: bool = False,
            is_transparent_background: bool = False
        ) -> np.ndarray:
        """
        Render this clip as a background at a given global time.

        Args:
            t_global: Global time in seconds
            target_width: Target width
            target_height: Target height
            will_need_blending: Whether subsequent clips will be blended on top
            high_precision_blending: Use float32 (True) or uint8 (False) for blending
            is_transparent_background: Whether to create transparent background

        Returns:
            This clip rendered for being a background
        """
        t_rel = (t_global - self._start)

        if not (0 <= t_rel < self.duration):
            raise RuntimeError("A background clip must be active")

        t_playback = t_rel * self._speed
        frame = self.get_frame(t_playback)
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
            mask_x, mask_y = round(mask_x), round(mask_y)
            mask_opacity_multiplier = self._mask.opacity(t_rel)

        x, y = self.position(t_rel)
        x, y = round(x), round(y)
        alpha_multiplier = self.opacity(t_rel)

        H, W = target_height, target_width
        h, w = frame.shape[:2]

        has_target_size = h == H and w == W
        has_custom_position = x != 0 or y != 0
        need_blending = alpha_multiplier != 1.0 or mask is not None or frame.shape[2] == 4
        matches_transparency_criteria = (frame.shape[2] == 4 and is_transparent_background) or (frame.shape[2] == 3 and not is_transparent_background)

        if (has_target_size and not has_custom_position and not need_blending and matches_transparency_criteria):
            # Possible improvment to research about:
            #  When will_need_blending is True, we are allocating a new chunk in memory for the whole frame in float32
            #  However, this allocation + copy in numpy, could be slower than:
            #   1. using our empty frame already reserved
            #   2. copying the 'frame' into this empty frame array using numba
            #   3. using memset(0) over the empty frame at the end of the loop (fill(0))
            if will_need_blending:
                return frame.astype(np.float32) if high_precision_blending else frame.copy()
            else:
                return frame
        
        if ((not has_target_size or has_custom_position) and not need_blending and matches_transparency_criteria):
            # it has custom position or different size, but doesn't need blending
            # this seems to be a bit faster that iterate the whole frame using numba in blending loop
            return crop_and_pad(frame, (H, W), (x, y), will_need_blending, high_precision_blending)

        y1_bg = max(y, 0)
        x1_bg = max(x, 0)
        y2_bg = min(y + h, H)
        x2_bg = min(x + w, W)

        if y1_bg >= y2_bg or x1_bg >= x2_bg:
            dtype = np.float32 if (will_need_blending and high_precision_blending) else np.uint8
            return empty_frame.get(dtype, W, H, 4 if is_transparent_background else 3).frame

        # Frame coordinates
        y1_fr = y1_bg - y
        x1_fr = x1_bg - x
        y2_fr = y2_bg - y
        x2_fr = x2_bg - x

        dtype = np.float32 if (will_need_blending and high_precision_blending) else np.uint8
        ef = empty_frame.get(dtype, W, H, 4 if is_transparent_background else 3)
        bg = ef.frame
        roi = bg[y1_bg:y2_bg, x1_bg:x2_bg]
        sub_fr = frame[y1_fr:y2_fr, x1_fr:x2_fr]

        if bg.shape[2] == 3:
            blend_foreground_with_bgr_background_inplace(roi, sub_fr, x, y, alpha_multiplier, mask, mask_x, mask_y, mask_opacity_multiplier)
        else:
            blend_foreground_with_bgra_background_inplace(roi, sub_fr, x, y, alpha_multiplier, mask, mask_x, mask_y, mask_opacity_multiplier)

        ef.mark_as_dirty()

        return bg

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

        if not (0 <= t_rel < self.duration):
            return bg

        t_playback = t_rel * self._speed
        frame = self.get_frame(t_playback)
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
            mask_x, mask_y = round(mask_x), round(mask_y)
            mask_opacity_multiplier = self._mask.opacity(t_rel)

        x, y = self.position(t_rel)
        x, y = round(x), round(y)
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

def apply_batched_pixel_transforms(frame: np.ndarray, transforms: list, t_rel: float) -> np.ndarray:
    """
    Apply multiple pixel transformations efficiently in a single pass.

    Args:
        frame: Input frame (BGR/BGRA uint8)
        transforms: List of numba-compiled transform functions
        t_rel: Relative time

    Returns:
        Transformed frame (BGR/BGRA uint8)
    """
    # Make a copy for in-place modification
    result = frame.copy()

    # Apply all transforms in a single numba loop
    _apply_pixel_transforms_inplace(result, transforms, t_rel)

    return result

@numba.jit(nopython=True, cache=True)
def _apply_pixel_transforms_inplace(frame, transforms, t_rel):
    """
    Apply pixel transforms in-place.
    Works with both BGR and BGRA frames.

    Note: Uses numba.jit (not njit) to allow calling numba-compiled callbacks.

    Args:
        frame: Frame to modify (BGR/BGRA uint8)
        transforms: List of numba-compiled transform functions
        t_rel: Relative time
    """
    height, width, channels = frame.shape
    has_alpha = channels == 4

    for y in range(height):
        for x in range(width):
            b = int(frame[y, x, 0])
            g = int(frame[y, x, 1])
            r = int(frame[y, x, 2])
            a = int(frame[y, x, 3]) if has_alpha else 255

            # Apply all transforms sequentially
            for transform in transforms:
                b, g, r = transform(b, g, r, a, t_rel)

            # Clamp and assign
            frame[y, x, 0] = min(255, max(0, b))
            frame[y, x, 1] = min(255, max(0, g))
            frame[y, x, 2] = min(255, max(0, r))

def crop_and_pad(frame: np.ndarray, target_size: tuple[int, int], position: tuple[int, int], will_need_blending: bool, high_precision_blending: bool) -> np.ndarray:
    target_h, target_w = target_size
    frame_h, frame_w, frame_c = frame.shape
    pos_x, pos_y = position

    if frame_h >= target_h and frame_w >= target_w and pos_x == 0 and pos_y == 0:
        final_frame = frame[:target_h, :target_w]
        if will_need_blending:
            return final_frame.astype(np.float32) if high_precision_blending else final_frame.copy()
        else:
            return final_frame

    dtype = np.float32 if (will_need_blending and high_precision_blending) else np.uint8
    ef = empty_frame.get(dtype, target_w, target_h, frame_c)
    canvas = ef.frame

    src_y_start = max(0, -pos_y)
    src_x_start = max(0, -pos_x)

    src_y_end = min(frame_h, target_h - pos_y)
    src_x_end = min(frame_w, target_w - pos_x)

    dest_y_start = max(0, pos_y)
    dest_x_start = max(0, pos_x)
    
    dest_y_end = min(target_h, pos_y + frame_h)
    dest_x_end = min(target_w, pos_x + frame_w)

    if src_y_end > src_y_start and src_x_end > src_x_start:
        canvas[dest_y_start:dest_y_end, dest_x_start:dest_x_end] = frame[src_y_start:src_y_end, src_x_start:src_x_end]
        ef.mark_as_dirty()

    return canvas

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
