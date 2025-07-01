from ipywidgets import Dropdown, SelectMultiple, Checkbox, VBox
from IPython.display import display


def create_dropdown(description, options):
    """
    Creates and returns an ipywidgets Dropdown with the given description and options.

    Parameters:
    - description (str): The text displayed next to the dropdown.
    - options (list): A list of strings representing the available choices.

    Returns:
    - Dropdown widget
    """
    dropdown = Dropdown(
        options=options,
        description=description,
        layout={'width': 'max-content'},  # Show full answers
        style={'description_width': 'initial'}  # Show full question
    )
    return dropdown


