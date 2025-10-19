from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel, ConfigDict

class Direction(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    UP = "up"
    DOWN = "down"

class OvershootConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    amount: float = 0.1
    peak_at: float = 0.7

class Transformer:
    LINEAR = lambda t: t
    EASE_IN = lambda t: t**2
    EASE_OUT = lambda t: 1 - (1 - t)**2
    EASE_IN_OUT = lambda t: t**2 * (3 - 2 * t)
    INVERT = lambda t: 1 - t
