# Supplementary code to article
This folder contains an object-oriented implementation of the metadata framework in python. All code is organized in jupyter notebooks. This version of the scripts was used to create the output referenced in the article "A Framework for using Metadata to Combine Data Sets in Official Statistics" (currently under review).

For new users, we recommend starting with the notebook classes_examples.ipynb. It contains examples and explanations of the most important concepts of the implementation. 

Case studies are applied in the notebook check_test_cases.ipynb. From within that notebook, you may select one of the existing test_case notebooks. The notebook test_case_mobility.ipynb contains all specifications required for the mobility use case. For implementing your own example, make a copy of test_case_mobility.ipynb and specify your own data, relations and models.

The notebook classes.ipynb contains all objects used in the implementation and may be interesting for precise definitions and further development.

For the most recent code, we refer to the scripts in python/essnet/ where the python code is ordered in a package structure and a pre-defined example is accesible in a user friendly notebook.