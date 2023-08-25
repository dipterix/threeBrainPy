import numpy as np

def hexstr_to_rgb(hexstr, max_value = 1.0):
    '''
    Convert a hex string to a numpy (RGBA) array.
    @param hexstr: The hex string.
    @param max_value: The maximum value of the RGB channels. (default: 1.0)
        Alpha channel is always maximized at 1.0
    '''
    if hexstr is None:
        return None
    if not isinstance(hexstr, str):
        raise TypeError(f"Invalid hex string: {hexstr}")
    if len(hexstr) < 3:
        raise ValueError(f"Invalid hex string: {hexstr}")
    hexstr = hexstr.lower()
    if hexstr.startswith("0x"):
        hexstr = hexstr[2:]
    elif hexstr.startswith("#"):
        hexstr = hexstr[1:]
    if not len(hexstr) in (3, 6, 8):
        raise ValueError(f"Cannot parse hex string: {hexstr}")
    if len(hexstr) == 3:
        hexstr = "".join([hexstr[i] * 2 for i in range(3)])
    if len(hexstr) == 6:
        hexstr = hexstr + "ff"
    R = int(hexstr[0:2], 16) * (max_value / 255)
    G = int(hexstr[2:4], 16) * (max_value / 255)
    B = int(hexstr[4:6], 16) * (max_value / 255)
    A = int(hexstr[6:8], 16) / 255
    return np.array([R,G,B,A], dtype=float)

def hex_to_rgb(x : list[str], max_value = 1.0):
    if isinstance(x, str):
        x = [x]
    return [hexstr_to_rgb(color) for color in x]


def interpolate_colors(x, n, truncate = False):
    '''
    Linearly interpolate colors.
    @param x: A list of colors in numpy arrays (RGB).
    @param n: The number of colors to interpolate.
    '''
    x = np.array(x, dtype=float)
    x_shape = x.shape
    if x_shape[1] != 4 and x_shape[1] != 3:
        raise ValueError(f"Invalid color shape: {x_shape}")
    if x_shape[0] < 2:
        raise ValueError(f"Invalid number of colors: {x_shape[0]}")
    if n < 2 or (truncate and n <= x_shape[0]):
        return x[0:n, :]
    nrows = x_shape[0]
    # i = 0 : (n-1)
    def get_color(i):
        pos = i * (nrows - 1.0) / (n - 1.0)
        i0 = int(np.floor(pos))
        if i0 < 0:
            return x[0, :]
        i1 = i0 + 1
        a = pos - i0
        if a < 1e-6 or i1 >= nrows:
            return x[i0, :]
        return x[i0, :] * (1-a) + x[i1, :] * a
    return np.array([get_color(i) for i in range(n)], dtype=float)

def arrays_to_rgb(x, max_value = 1.0, prefix = "#", drop_alpha = True):
    '''
    Convert a list of numpy arrays to a list of hex strings.
    '''
    np.array(x, dtype=float)
    if x.shape[1] != 4 and x.shape[1] != 3:
        raise ValueError(f"Invalid color shape: {x.shape}")
    def as_hex(d):
        d = (d / max_value * 255)
        d[d < 0] = 0
        d[d > 255] = 255
        for i in d.astype(np.uint8):
            hexstr = hex(i)[2:]
            if len(hexstr) == 1:
                yield f"0{hexstr}"
            else:
                yield hexstr[:2]
    R = as_hex(x[:,0])
    G = as_hex(x[:,1])
    B = as_hex(x[:,2])
    if not drop_alpha and x.shape[1] == 4:
        A = as_hex(x[:,3])
        return [f"{prefix}{r}{g}{b}{a}" for r,g,b,a in zip(R,G,B,A)]
    else:
        return [f"{prefix}{r}{g}{b}" for r,g,b in zip(R,G,B)]
