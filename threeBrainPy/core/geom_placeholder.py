# Blank placeholder for geom to hold group data only

from .geom_template import GeometryTemplate

class BlankPlaceholder ( GeometryTemplate ):
    def __init__(self, brain, is_global : bool = False) -> None:
        '''
        R code:
        self$globals <- BlankGeom$new(
            group = GeomGroup$new(name = sprintf('_internal_group_data_%s', subject_code)),
            name = sprintf('_misc_%s', subject_code)
        )
        '''
        if is_global:
            name = "__blank__"
            group_name = "__global_data"
        else:
            name = f"_misc_{brain.subject_code}"
            group_name = f"_internal_group_data_{brain.subject_code}"
        super().__init__(brain = brain, name = name, group_name = group_name, auto_register = not is_global)
        # set to a hidden layer so that it won't be displayed
        self.set_layers( 31 )
        self.clickable = False
    @property
    def type(self):
        return "blank"
        