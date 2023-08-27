# from shiny import App, ui
# from shiny import ui
# from shinywidgets import output_widget, render_widget

# app_ui = ui.page_fixed(
#     output_widget("my_widget")
# )

# # Part 2: server ----
# from threebrainpy.extensions import BrainWidget
# from threebrainpy.core import Brain
# def server(input, output, session):

#     w = BrainWidget()

#     @output
#     @render_widget
#     def my_widget():
#         brain = Brain("test", "/Users/dipterix/rave_data/raw_dir/DemoSubject/rave-imaging/fs")
#         brain.add_slice(slice_prefix = "brain.finalsurfs")
#         # self._groups['Volume - T1 (test)']._cached_items
#         brain.add_surfaces(surface_type = "pial")
#         w.render(brain)
#         return w

# # Combine into a shiny app.
# # Note that the variable must be "app".
# app = App(app_ui, server)
# import shiny
# shiny.run_app(app, launch_browser=True)