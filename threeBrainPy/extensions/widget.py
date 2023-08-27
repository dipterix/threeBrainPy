import json
from .._version import NPM_PACKAGE_RANGE
from ..utils.service import start_service
from ..utils.validator import validate_css_size
from ..core import Brain

try:
    import ipywidgets as widgets
    from traitlets import Unicode
    @widgets.register
    class BrainWidget(widgets.DOMWidget):
        # Name of the widget view class in front-end
        _view_name = Unicode('BrainWidgetView').tag(sync=True)
        # Name of the widget model class in front-end
        _model_name = Unicode('BrainWidgetModel').tag(sync=True)
        # Name of the front-end module containing widget view
        _view_module = Unicode('threebrainpy').tag(sync=True)
        # Name of the front-end module containing widget model
        _model_module = Unicode('threebrainpy').tag(sync=True)
        # Version of the front-end module containing widget view
        _view_module_version = Unicode(NPM_PACKAGE_RANGE).tag(sync=True)
        # Version of the front-end module containing widget model
        _model_module_version = Unicode(NPM_PACKAGE_RANGE).tag(sync=True)
        # Widget specific property.
        # Widget properties are defined as traitlets. Any property tagged with `sync=True`
        # is automatically synced to the frontend *any* time it changes in Python.
        # It is synced back to Python from the frontend *any* time the model is touched.
        config = Unicode("").tag(sync=True)
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        def render(self, brain : Brain, width = "100%", height = 500, **kwargs : dict):
            if not isinstance(brain, Brain):
                raise TypeError(f"Expected a Brain object, but got {type(brain)}")
            width, width_unit = validate_css_size(width)
            height, height_unit = validate_css_size(height)
            if width_unit in ("%", "vh", "vw"):
                width = width / 100
            if height_unit in ("%", "vh", "vw"):
                height = height / 100
            service = start_service()
            # build the brain into service directory
            config = brain.build(path = service._directory, dry_run = False, **kwargs)
            self.service = service
            self.brain = brain
            cache_folder = config["settings"]["cache_folder"]
            config["settings"]["cache_folder"] = f"http://{service.url}/{cache_folder}/"
            config["width"] = width
            config["height"] = height
            self.config = json.dumps(config)
            return self
    pass
except Exception as e:
    class BrainWidget():
        def __init__(self) -> None:
            raise ModuleNotFoundError("ipywidgets not installed. Please install Python package `ipywidgets` to use BrainWidget.")
