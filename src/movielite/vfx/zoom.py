from ..core import GraphicClip
from .base import GraphicEffect
from typing import Union, Tuple

class ZoomIn(GraphicEffect):
    """
    Zoom-in effect that gradually scales up the clip from a smaller size.
    """

    def __init__(
        self,
        duration: float,
        from_scale: float = 1.0,
        to_scale: float = 1.2,
        anchor: str = "center"
    ):
        """
        Create a zoom-in effect.

        Args:
            duration: Duration of the zoom effect in seconds
            from_scale: Starting scale (1.0 = 100% size)
            to_scale: Ending scale (1.2 = 120% size)
            anchor: Zoom anchor point. Options:
                   'center' (default), 'top-left', 'top-right',
                   'bottom-left', 'bottom-right', 'top', 'bottom', 'left', 'right'
                   or tuple (x, y) for custom anchor in clip coordinates
        """
        self.duration = duration
        self.from_scale = max(0.1, from_scale)
        self.to_scale = to_scale
        self.anchor = anchor

    def apply(self, clip: GraphicClip) -> None:
        """Apply zoom-in effect by modifying the clip's scale and position"""
        original_scale = clip._scale
        original_position = clip._position

        # Get clip size (after any resize transformations)
        clip_width, clip_height = clip.size

        def scale_with_zoom_in(t):
            if t >= self.duration:
                return original_scale(t) * self.to_scale

            # Linear interpolation from from_scale to to_scale
            progress = t / self.duration
            current_scale = self.from_scale + (self.to_scale - self.from_scale) * progress
            return original_scale(t) * current_scale

        def position_with_zoom_in(t):
            base_pos = original_position(t)

            if t >= self.duration:
                current_scale = self.to_scale
            else:
                progress = t / self.duration
                current_scale = self.from_scale + (self.to_scale - self.from_scale) * progress

            # Calculate anchor point in clip coordinates
            anchor_x, anchor_y = _calculate_anchor_point(self.anchor, clip_width, clip_height)

            # Adjust position to keep anchor point fixed
            offset_x = anchor_x * (1 - current_scale)
            offset_y = anchor_y * (1 - current_scale)

            return (base_pos[0] + offset_x, base_pos[1] + offset_y)

        clip.set_scale(scale_with_zoom_in)
        clip.set_position(position_with_zoom_in)


class ZoomOut(GraphicEffect):
    """
    Zoom-out effect that gradually scales down the clip.
    """

    def __init__(
        self,
        duration: float,
        from_scale: float = 1.2,
        to_scale: float = 1.0,
        anchor: str = "center"
    ):
        """
        Create a zoom-out effect.

        Args:
            duration: Duration of the zoom effect in seconds
            from_scale: Starting scale (1.2 = 120% size)
            to_scale: Ending scale (1.0 = 100% size)
            anchor: Zoom anchor point. Options:
                   'center' (default), 'top-left', 'top-right',
                   'bottom-left', 'bottom-right', 'top', 'bottom', 'left', 'right'
                   or tuple (x, y) for custom anchor in clip coordinates
        """
        self.duration = duration
        self.from_scale = from_scale
        self.to_scale = max(0.1, to_scale)
        self.anchor = anchor

    def apply(self, clip: GraphicClip) -> None:
        """Apply zoom-out effect by modifying the clip's scale and position"""
        original_scale = clip._scale
        original_position = clip._position
        clip_duration = clip.duration

        # Get clip size (after any resize transformations)
        clip_width, clip_height = clip.size

        def scale_with_zoom_out(t):
            # Apply zoom out at the end of the clip
            if t < clip_duration - self.duration:
                return original_scale(t) * self.from_scale

            # Linear interpolation from from_scale to to_scale
            time_in_effect = t - (clip_duration - self.duration)
            progress = time_in_effect / self.duration
            current_scale = self.from_scale + (self.to_scale - self.from_scale) * progress
            return original_scale(t) * current_scale

        def position_with_zoom_out(t):
            base_pos = original_position(t)

            # Apply zoom out at the end of the clip
            if t < clip_duration - self.duration:
                current_scale = self.from_scale
            else:
                time_in_effect = t - (clip_duration - self.duration)
                progress = time_in_effect / self.duration
                current_scale = self.from_scale + (self.to_scale - self.from_scale) * progress

            # Calculate anchor point in clip coordinates
            anchor_x, anchor_y = _calculate_anchor_point(self.anchor, clip_width, clip_height)

            # Adjust position to keep anchor point fixed
            offset_x = anchor_x * (1 - current_scale)
            offset_y = anchor_y * (1 - current_scale)

            return (base_pos[0] + offset_x, base_pos[1] + offset_y)

        clip.set_scale(scale_with_zoom_out)
        clip.set_position(position_with_zoom_out)


class KenBurns(GraphicEffect):
    """
    Ken Burns effect: slow zoom + pan animation.
    Creates a cinematic feel by slowly zooming and panning across the image.
    """

    def __init__(
        self,
        duration: float = None,
        start_scale: float = 1.0,
        end_scale: float = 1.2,
        start_position: tuple[int, int] = (0, 0),
        end_position: tuple[int, int] = (0, 0)
    ):
        """
        Create a Ken Burns effect.

        Args:
            duration: Duration of the effect (None = entire clip duration)
            start_scale: Starting zoom level
            end_scale: Ending zoom level
            start_position: Starting position (x, y)
            end_position: Ending position (x, y)
        """
        self.duration = duration
        self.start_scale = start_scale
        self.end_scale = end_scale
        self.start_position = start_position
        self.end_position = end_position

    def apply(self, clip: GraphicClip) -> None:
        """Apply Ken Burns effect by modifying scale and position"""
        original_scale = clip._scale
        original_position = clip._position

        # Use entire clip duration if not specified
        effect_duration = self.duration if self.duration is not None else clip.duration

        def scale_with_ken_burns(t):
            if t >= effect_duration:
                return original_scale(t) * self.end_scale

            # Smooth easing (ease-in-out)
            progress = t / effect_duration
            # Cubic ease-in-out
            if progress < 0.5:
                eased_progress = 4 * progress * progress * progress
            else:
                eased_progress = 1 - pow(-2 * progress + 2, 3) / 2

            current_scale = self.start_scale + (self.end_scale - self.start_scale) * eased_progress
            return original_scale(t) * current_scale

        def position_with_ken_burns(t):
            if t >= effect_duration:
                base_pos = original_position(t)
                return (base_pos[0] + self.end_position[0], base_pos[1] + self.end_position[1])

            # Smooth easing (ease-in-out)
            progress = t / effect_duration
            # Cubic ease-in-out
            if progress < 0.5:
                eased_progress = 4 * progress * progress * progress
            else:
                eased_progress = 1 - pow(-2 * progress + 2, 3) / 2

            current_x = self.start_position[0] + (self.end_position[0] - self.start_position[0]) * eased_progress
            current_y = self.start_position[1] + (self.end_position[1] - self.start_position[1]) * eased_progress

            base_pos = original_position(t)
            return (int(base_pos[0] + current_x), int(base_pos[1] + current_y))

        clip.set_scale(scale_with_ken_burns)
        clip.set_position(position_with_ken_burns)

def _calculate_anchor_point(
    anchor: Union[str, Tuple[int, int]],
    clip_width: int,
    clip_height: int
) -> Tuple[float, float]:
    if isinstance(anchor, tuple):
        return anchor

    anchor_map = {
        "center": (clip_width / 2, clip_height / 2),
        "top-left": (0, 0),
        "top-right": (clip_width, 0),
        "bottom-left": (0, clip_height),
        "bottom-right": (clip_width, clip_height),
        "top": (clip_width / 2, 0),
        "bottom": (clip_width / 2, clip_height),
        "left": (0, clip_height / 2),
        "right": (clip_width, clip_height / 2)
    }

    return anchor_map.get(anchor, (clip_width / 2, clip_height / 2))