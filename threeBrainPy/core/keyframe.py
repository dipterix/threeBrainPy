import re
import numpy as np
from ..utils.constants import CONSTANTS

class SimpleKeyframe:
    def __init__(self, name, value, time = None, dtype = 'continuous', target = '.material.color', **kwargs) -> None:
        
        if not isinstance(name, str):
            raise TypeError("name must be a string")
        name = re.sub(r"[^a-zA-Z0-9_\\[\\]]", ".", name)
        if name in CONSTANTS.KEYFRAME_RESERVED_NAMES:
            raise ValueError(f"Invalid keyframe name, must not be reserved names {CONSTANTS.KEYFRAME_RESERVED_NAMES}.")
        
        value_dtype = float if dtype == 'continuous' else str
        self._dtype = 'continuous' if dtype == 'continuous' else 'discrete'
        self._name = name
        self._target = target
        self._value = np.array(value, dtype=value_dtype).reshape(-1)
        self._time = np.array(time, dtype=float).reshape(-1) if time is not None else None
        if self._time is None:
            if self._value.size != 1:
                raise ValueError("Value must be a scalar when time is None")
            self._time = np.array([0.0], dtype=float)
        elif len(self._time) != len(self._value):
            raise ValueError("Value, time lengths must equal unless time is None and value is a scalar")
        if self._dtype == 'continuous':
            # remove NAs and infinities
            sel = np.isfinite(self._value)
            self._time = self._time[sel]
            self._value = self._value[sel]
            self._implicit_levels = set()
        else:
            self._implicit_levels = set(self._value)
        self._levels = None
    @property
    def name(self):
        return self._name
    @property
    def target(self):
        return self._target
    @property
    def time(self):
        return self._time
    @property
    def value(self):
        return self._value
    @property
    def is_continuous(self):
        return self._dtype is 'continuous'
    @property
    def levels(self):
        '''
        The (factor) levels of the keyframe, i.e. a unique list of values when discrete.
        If the keyframe is continuous, this will be None.
        '''
        if self._dtype == 'continuous':
            return None
        if self._levels is None:
            return self._implicit_levels
        return self._levels
    def set_levels(self, levels):
        '''
        Set the levels of the keyframe. This is only valid for discrete keyframes.
        '''
        if self._dtype == 'continuous':
            return
        if levels is None:
            # use default
            self._levels = None
            return
        if isinstance(levels, str):
            levels = [levels]
        elif isinstance(levels, np.ndarray):
            levels = levels.reshape(-1)
        levels = set(levels).union(self._implicit_levels)
        self._levels = levels
    @property
    def range(self):
        if self._dtype == 'continuous':
            return np.array([np.min(self._value), np.max(self._value)])
        return None
    @property
    def time_range(self):
        if self._time is None:
            return None
        return np.array([np.nanmin(self._time), np.nanmax(self._time)])
    def to_dict(self):
        return {
            'name': self._name,
            'time': self._time,
            'value': self._value,
            'data_type': self._dtype,
            'target': self._target,
            'cached': False
        }


