from ipywidgets import Checkbox, VBox, Label, Button, Output
from IPython.display import display


class CheckboxData:
    def __init__(self, data_list, description="Select data sets:", print_full_name=False, single_option=False):
        self.data_list = data_list
        self.description = description
        self.single_option = single_option

        checkboxes = []  # initialise empty list of checkboxes
        counter = 0

        for data in self.data_list:
            # determine display name based on option print_full_name
            if print_full_name:
                tmp_name = str(data)
            else: 
                tmp_name = data.name

            # if single_option: only let the first box be checked on initalisation
            # if not single option: we want all boxed checked on initialisation
            if single_option and counter>0:
                tmp_value = False
            else:
                tmp_value = True

            # create check box
            checkboxes.append(Checkbox(
                # print data name and included variables
                description=tmp_name,
                value=tmp_value,  # start with a chekmark
                layout={'width': 'max-content'}
            ))

            counter += 1

        self.checkboxes = checkboxes  # set checkboxes

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
            # return a single data set (we know there is only one)
            return [data for data, checkbox in zip(self.data_list, self.checkboxes) if checkbox.value][0]
        else:
            # return a list of the selected data sets
            return [data for data, checkbox in zip(self.data_list, self.checkboxes) if checkbox.value]

    def on_checkbox_change(self, change):
        """Ensure only one checkbox is selected at a time. Enabled when single_option=True. """
        if change['new']:
            # If this checkbox is selected, uncheck all others
            for cb in self.checkboxes:
                if cb is not change['owner']:
                    cb.value = False
