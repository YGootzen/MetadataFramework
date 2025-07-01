from ipywidgets import Checkbox, VBox, Label, Button, Output
from IPython.display import display


class CheckboxModel:
    def __init__(self, model_list, description="Select available models:", print_full_name=False, single_option=False):
        self.model_list = model_list
        self.description = description
        self.single_option = single_option

        if print_full_name:
            self.checkboxes = [
                Checkbox(
                    # print model name with description of input and output data sets
                    description=str(model),
                    value=True,  # start with a chekmark
                    layout={'width': 'max-content'}
                )
                for model in self.model_list
            ]
        else:
            self.checkboxes = [
                Checkbox(
                    description=model.name,  # print name of model only
                    value=True,  # start with a checkmark
                    layout={'width': 'max-content'}
                )
                for model in self.model_list
            ]

        # Set up the event handlers for checkboxess
        if self.single_option:
            for checkbox in self.checkboxes:
                checkbox.observe(self.on_checkbox_change, names='value')

        # Layout
        self.label = Label(self.description)
        self.checkbox_box = VBox(self.checkboxes)
        self.checkbox_group = VBox(
            [self.label, self.checkbox_box])

    def display(self):
        display(self.checkbox_group)

    def get_selected(self):
        if self.single_option:
            # return a single model (we know there is only one)
            return [model for model, checkbox in zip(self.model_list, self.checkboxes) if checkbox.value][0]
        else:
            # return a list of the selected models
            return [model for model, checkbox in zip(self.model_list, self.checkboxes) if checkbox.value]

    def on_checkbox_change(self, change):
        """Ensure only one checkbox is selected at a time. Enabled when single_option=True. """
        if change['new']:
            # If this checkbox is selected, uncheck all others
            for cb in self.checkboxes:
                if cb is not change['owner']:
                    cb.value = False
