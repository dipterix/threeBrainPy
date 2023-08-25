import json
import numpy as np
from json import JSONEncoder



class GeomEncoder(JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "to_json"):
            return json.loads(obj.to_json(cls = GeomEncoder))
        elif hasattr(obj, "to_dict"):
            return obj.to_dict()
        elif hasattr(obj, "to_list"):
            return obj.to_list()
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return dict([(k, self.default(v)) for k, v in obj.items()])
        elif isinstance(obj, (list, tuple)):
            return [self.default(v) for v in obj]
        else:
            try:
                iterable = iter(obj)
            except TypeError:
                return super().default(obj)
            else:
                return list(iterable)
