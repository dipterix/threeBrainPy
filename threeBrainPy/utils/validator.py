import re
def validate_css_size(x):
    x = str(x)
    m = re.match(r"^([0-9.]+)[ ]{0,}(|px|vh|vw|%)$", x)
    if not m:
        raise ValueError(f"Invalid CSS size: {x}")
    size, unit = m.groups()
    if unit in ("%", "vh", "vw"):
        size = float(size)
    else:
        size = int(float(size))
        unit = "px"
    if size < 0:
        raise ValueError(f"Invalid CSS size: {x}")
    return (size, unit,)
    
