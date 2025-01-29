from typing import Union
import numpy as np
from .keyframe import SimpleKeyframe
from .constants import CONSTANTS
from ..utils.color import hex_to_rgb, interpolate_colors, arrays_to_rgb

class ElectrodeColormap:
    def __init__(self, keyframe_name : str, value_type : str, alias : str = None) -> None:
        if isinstance(keyframe_name, SimpleKeyframe):
            self.name = keyframe_name.name
            self._value_type = "continuous" if keyframe_name.is_continuous else "discrete"
        else:
            self.name = keyframe_name
            self._value_type = value_type
        if not self._value_type in ("continuous", "discrete"):
            raise ValueError(f"Invalid value type: {self._value_type}")
        self.alias = self.name if alias is None else alias
        self._time_range = np.array([0, 0], dtype=float)
        # for continuous value, the value_range is a list of two floats
        self._value_range = np.array([0, 0], dtype=float)
        # for descrete value, the value_names is a list of strings
        self._value_names = set()
        # Theoretical range, like p-value, cannot goes below 0 nor beyond 1, hence (0,1)
        self._hard_range = None
        # suggested number of colors, default is 64
        # for discrete value, the number of colors is the number of levels (up-scaled to nearest power of 2)
        # for continuous value, the number of colors is the number of colors in the palette
        self._n_colors = 64
        # color arrays (nx3 or nx4)
        self._cmap = None
        self._initialized = False
        self.symmetrical = True
        # keyframes with time stamp and values
        self._keyframes = {}
        if isinstance(keyframe_name, SimpleKeyframe):
            self.update_from_keyframe( keyframe_name )
    def update_from_keyframe(self, keyframe : SimpleKeyframe, ignore_name : bool = False):
        if not isinstance(keyframe, SimpleKeyframe):
            return
        if keyframe.name != self.name and not ignore_name:
            raise ValueError(f"keyframe name {keyframe.name} does not match colormap name {self.name} when ignore_name=False")
        if self._value_type is None:
            self._value_type = "continuous" if keyframe.is_continuous else "discrete"
        elif self._value_type != "continuous" and keyframe.is_continuous:
            raise ValueError(f"keyframe {keyframe.name} is continuous but colormap {self.name} is discrete")
        elif self._value_type != "discrete" and not keyframe.is_continuous:
            raise ValueError(f"keyframe {keyframe.name} is discrete but colormap {self.name} is continuous")
        # update time range
        if isinstance(keyframe.time_range, np.ndarray):
            time_min = keyframe.time_range[0]
            time_max = keyframe.time_range[1]
            if np.isfinite(time_min):
                if self._initialized:
                    self._time_range[0] = np.nanmin([self._time_range[0], time_min])
                else:
                    self._time_range[0] = time_min
            if np.isfinite(time_max):
                if self._initialized:
                    self._time_range[1] = np.nanmax([self._time_range[1], time_max])
                else:
                    self._time_range[1] = time_max
        if keyframe.is_continuous:
            # update value range if continuous
            value_min = keyframe.range[0]
            value_max = keyframe.range[1]
            if np.isfinite(value_min):
                if self._initialized:
                    value_min = np.nanmin([self._value_range[0], value_min])
            if np.isfinite(value_max):
                if self._initialized:
                    value_min = np.nanmax([self._value_range[1], value_max])
            if self._hard_range is not None:
                value_min = np.max([value_min, self._hard_range[0]])
                value_max = np.min([value_max, self._hard_range[1]])
            self._value_range[0] = value_min
            self._value_range[1] = value_max
        else:
            # update value names if discrete
            self._value_names = self._value_names.union(keyframe.levels)
        self._initialized = True
    
    def update_from_electrodes(self, *args) -> Union[list[SimpleKeyframe], None]:
        from ..geom.sphere import ElectrodeSphere
        for contact in args:
            if isinstance(contact, ElectrodeSphere):
                keyframe = contact._keyframes.get(self.name, None)
                if not self._initialized or ((keyframe.is_continuous) ^ (self._value_type == "continuous") == 0):
                    self.update_from_keyframe(keyframe)
                    yield keyframe
            
    @property
    def value_type(self):
        return self._value_type
    @property
    def time_range(self):
        if not self._initialized:
            return np.array([0., 1.], dtype=float)
        tmin = self._time_range[0]
        tmax = self._time_range[1]
        if np.isfinite(tmin) and np.isfinite(tmax):
            if tmin == tmax:
                tmax += 1
        elif np.isfinite(tmin):
            tmax = tmin + 1
        elif np.isfinite(tmax):
            tmin = tmax - 1
        else:
            return np.array([0., 1.], dtype=float)
        return np.array([tmin, tmax], dtype=float)
    def get_value_range(self, underlying = False):
        if not underlying and self._hard_range is not None:
            return self._hard_range.copy()
        if not self._initialized or self._value_type == "discrete":
            return np.array([-1., 1.], dtype=float)
        is_sym = False
        sym = 0
        if isinstance(self.symmetrical, bool):
            if self.symmetrical:
                sym = 0
                is_sym = True
        elif isinstance(self.symmetrical, (int, float)):
            sym = self.symmetrical
            is_sym = True
        vmin = self._value_range[0] - sym
        vmax = self._value_range[1] - sym
        
        if is_sym:
            if np.isfinite(vmin) or np.isfinite(vmax):
                vmax = np.nanmax(np.abs([vmin, vmax]))
                if vmax == 0:
                    vmax = 1.0
                vmin = -vmax
            else:
                vmin = -1.0
                vmax = 1.0
        else:
            if np.isfinite(vmin) and np.isfinite(vmax):
                if vmin == vmax:
                    vmax += 1
            elif np.isfinite(vmin):
                vmax = vmin + 1
            elif np.isfinite(vmax):
                vmin = vmax - 1
            else:
                vmin = -1.0
                vmax = 1.0
        return np.array([vmin + sym, vmax + sym], dtype=float)
    @property
    def value_range(self):
        return self.get_value_range(underlying=False)
    @property
    def value_names(self):
        if not self._initialized or self._value_type == "continuous":
            return tuple()
        return tuple(self._value_names)
    
    def set_hard_range(self, value) -> Union[np.ndarray, None]:
        if value is None:
            self._hard_range = None
            return None
        if isinstance(value, (list, tuple)):
            value = np.array(value, dtype=float)
        if not isinstance(value, np.ndarray):
            raise ValueError(f"Invalid hard_range type: {type(value)}")
        if value.size != 2:
            raise ValueError(f"Invalid hard_range size: {value.size}")
        if not np.isfinite(value).all():
            raise ValueError(f"Invalid hard_range value: {value}")
        self._hard_range = value.copy().reshape((2, ))
    @property
    def n_colors(self):
        '''
        The JavaScript engine only accepts power of 2 number of colors.
        '''
        n = self._n_colors
        if self._value_type == "discrete":
            n = len(self._value_names)
        if n < 2:
            n = 2
        return int(np.power(2, np.ceil(np.log2(n))))
    @n_colors.setter
    def n_colors(self, value):
        value = int(value)
        if value < 2:
            raise ValueError(f"Invalid n_colors: {value}")
        self._n_colors = value
    def use_colors(self, x, method = ["auto", "hex", "array", "matplotlib"]):
        '''
        The generate colors from the palette.
        @param x: Can be one of the followings:
            1. A list of colors in hex string format, e.g. ["#ff0000", "#00ff00", "#0000ff"]
            2. A numpy array (n, p) of colors in RGB(A) format (p = 3 or 4), 
                e.g. np.array([[1,0,0], [0,1,0], [0,0,1]])
                The max values of the RGB(A) must be 1.0
            3. The name of the palette, e.g. "rainbow", this requires `matplotlib` to be installed
                We will look for the color map from matplotlib
            4. A list of color maps
        @param method: The method to use to generate colors, can be one of the followings:
            auto: try to guess the method
            hex: use x as hex string
            array: use x as numpy array
            matplotlib: use x as matplotlib color map(s) or map name(s)
        '''
        if isinstance(method, (list, tuple, )):
            if len(method) == 0:
                method = "auto"
            else:
                method = method[0]
        if method is None or method not in ("auto", "hex", "array", "matplotlib", ):
            method = "auto"
        if method == "auto":
            # guess the method
            if isinstance(x, str):
                method = "matplotlib"
                x = [x]
            elif isinstance(x, np.ndarray):
                method = "array"
            elif isinstance(x, (list, tuple,)):
                if len(x) == 0:
                    method = "hex"
                elif isinstance(x[0], str):
                    if x[0].startswith("#") or x[0].startswith("0x"):
                        method = "hex"
                    else:
                        method = "matplotlib"
                elif isinstance(x[0], (list, tuple, np.ndarray)):
                    method = "array"
                else:
                    method = "matplotlib"
            else:
                method = "matplotlib"
                x = [x]
        
        n_colors = self.n_colors
        if method == "hex":
            x = hex_to_rgb(x)
        elif method == "matplotlib":
            from matplotlib import pyplot as plt
            # x is in list now
            n_sub = int(np.ceil(n_colors / len(x)))
            colors = []
            for cmap in x:
                if isinstance(cmap, str):
                    cmap = plt.get_cmap( cmap )
                cmap = cmap.resample(n_sub)
                for i in range(n_sub):
                    colors.append(cmap(i))
            x = colors
        # now x is in numpy array
        self._cmap = np.array(x, dtype=float)
    def generate_colors(self, as_hex = True, **kwargs) -> Union[dict, None]:
        assert self._initialized, "Colormap not initialized."
        vtype = self._value_type
        if self._cmap is None:
            if vtype == "continuous":
                self.use_colors(CONSTANTS.COLORMAP_DEFAULT_CONTINUOUS)
            else:
                self.use_colors(CONSTANTS.COLORMAP_DEFAULT_DISCRETE)
        n_colors = self.n_colors
        if vtype == "continuous":
            colors = interpolate_colors(self._cmap, n_colors)
            vrange = self.value_range
            keys = np.linspace(vrange[0], vrange[1], num=n_colors)
        else:
            colors = interpolate_colors(self._cmap, n_colors, truncate=True)
            keys = np.linspace(0, 1, num=n_colors)
        if as_hex:
            colors = arrays_to_rgb(colors, **kwargs)
        return {
            "keys": keys,
            "colors": colors
        }
    def __repr__(self) -> str:
        if not self._initialized:
            return f"<{self.__class__.__name__}: {self.name} (uninitialized)>"
        return f"<{self.__class__.__name__}: {self.name} ({self._value_type}, N={self.n_colors})>"
    def to_dict(self) -> dict:
        if not self._initialized:
            return {}
        pals = self.generate_colors(as_hex=True, prefix="0x", drop_alpha=True)
        data = {
            "name": self.name,
            "alias": self.alias,
            "time_range": self.time_range.tolist(),
            "value_type": self._value_type,
            # Continuous
            "value_range": self.value_range.tolist(),
            "hard_range" : self._hard_range.tolist() if self._hard_range is not None else None,
            # discrete
            "value_names": self.value_names,
            "color_levels": len(self._value_names),

            "color_keys": pals["keys"].tolist(),
            "color_vals": pals["colors"],
        }
        return data

