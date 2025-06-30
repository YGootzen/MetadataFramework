import pandas as pd


def legend_print(legend):
    """
    Pretty prints the legend dictionary for variables and granularities.
    """
    print("\033[1m----------Variables and granularities (legend)----------\033[0m")
    for key_var, legend_var in legend.items():
        print(key_var + ": " + legend_var["name"])

        for key_gran, name_gran in legend_var["granularities"].items():
            if not (key_gran == 0 and name_gran == ""):
                print("   " + str(key_var)+str(key_gran) + ": " + str(name_gran))

def path_print(path):
    """
    Pretty print the path output from the search algorithm.
    """

    path_print_data_list = []
    for i in range(len(path)):
        path_dict = {"step": "step "+str(i),
                     "method": str(path[i].method),
                     "method_detail": str(path[i].method_detail),
                     "input": [str(data_in) for data_in in path[i].input],
                     "output": [str(data_out) for data_out in path[i].output]}

        data_add = pd.DataFrame(
            dict([(k, pd.Series(v)) for k, v in path_dict.items()]))
        path_print_data_list.append(data_add)

        # path_print_data.append(data_add)
    path_print_data = pd.concat(path_print_data_list, ignore_index=True)
    path_print_data = path_print_data.fillna("")

    return path_print_data








