"""
# A* implementation
This script contains an implementation of the A* algorithm. It is based on the 
similarity score function of the set of available data sources, which is in turn 
based on (a combination of) the similarity score function for data sources. 
"""

import copy
import time
import numpy as np

from metadata_analysis.metadata.aggregation import AggregationGraph
from metadata_analysis.metadata.variable import Variable
from metadata_analysis.metadata.model import ModelSingleUse
from metadata_analysis.metadata.path_step import Step


def get_scores(similarity_choice, open_list, goal, variant="base", prints=False, score_function_parameter=None):
    # from all possible variants for the available set of data sources, take the one with the highest similarity score
    if similarity_choice == "sum":
        all_scores = [temp_set.similarity_sum(goal, variant=variant) for temp_set in open_list]
    elif similarity_choice == "topsum":
        all_scores = [temp_set.similarity_topsum(goal, variant=variant, prints=prints, multiplier=score_function_parameter) for temp_set in open_list]
    elif similarity_choice == "max":
        all_scores = [temp_set.similarity_max(goal, variant=variant) for temp_set in open_list]
    elif similarity_choice == "mean":
        all_scores = [temp_set.similarity_mean(goal, variant=variant) for temp_set in open_list]
    elif similarity_choice == "median":
        all_scores = [temp_set.similarity_median(goal, variant=variant) for temp_set in open_list]
    elif similarity_choice == "min":
        all_scores = [temp_set.similarity_min(goal, variant=variant) for temp_set in open_list]
    elif similarity_choice == "minmax":
        all_scores = [temp_set.similarity_minmax(goal, variant=variant) for temp_set in open_list]
    elif similarity_choice == "maxmean":
        all_scores = [temp_set.similarity_maxmean(goal, variant=variant) for temp_set in open_list]
    elif similarity_choice == "maxmeanmin":
        all_scores = [temp_set.similarity_maxmeanmin(goal, variant=variant) for temp_set in open_list]
    elif similarity_choice == "max_per_variable":
        all_scores = [temp_set.similarity_max_per_variable(goal, variant=variant) for temp_set in open_list]
    elif similarity_choice == "max_per_variable_bonus":
        all_scores = [temp_set.similarity_max_per_variable_bonus(goal, variant=variant) for temp_set in open_list]
    else: 
        print("No known similarity score option was chosen")
        return False
    
    return all_scores


def prep_rhs(start_set, goal):
    """
    This function takes the starting set of available sources and will for each source, aggregate it as 
    far as possible to match the right hand side of the end goal.
    """
    start_set_copy = copy.deepcopy(start_set)
    vars_left = []   # all lhs variables in start_set with a rhs that can be aggregated to the goal rhs

    for data_source in start_set.set_of_sources:
        # for each of the data sources, we'll check if we can aggregate (some of) it's rhs variables to match the goal rhs
        data_source_new = copy.deepcopy(data_source)
        path_steps = []  # for explaining the step in the path, all aggregation details

        for v_r in data_source.right_variables:
            # check if one of the goal rhs variables can be reached by this variable
            
            aggregation_graph = AggregationGraph.get(v_r.name)  # loop up corresponding aggregation graph
            connected_granularities = aggregation_graph.all_aggregations(v_r.granularity)
            for g in connected_granularities:
                v2 = Variable(name=v_r.name, granularity = g)  # copy the name, but use the new granularity

                if v2 in goal.right_variables:
                    # a rhs variable of the goal is reached! 
                    path_step_tmp = data_source_new.aggregate_variable(var_remove = v_r, var_add = v2)
                    # add to the method_detail for the path:
                    path_steps.append(path_step_tmp)

                    # there should only be one (since variable names should only occur once in the rhs)
                    break # step out of the v_r for loop
        if data_source_new!=data_source:
            # some change has been made by the rhs preprocessing
            # once all variables have been checked, we can add the data_source_new to the new start_set

            start_set_copy.add_data_source(data_source_new, path_step=path_steps)
            
    return start_set_copy


def a_star(start_set, goal, models, max_iteration, similarity_choice = "sum", prints=False, 
          preprocess_rhs = False, find_multiple_paths=False, shedding=False, shedding_n = 10, variant="base", score_function_parameter=None):

    if prints: print("Starting A* function, goal:" + str(goal))
    
    # initialize open and closed lists
    open_list = []
    closed_list = []
    success_list = []
    current_set = start_set    # for printing update
    previous_score = -1

    # Apply the single use models in models
    models_multiple_use = []
    for m in models:
        if isinstance(m, ModelSingleUse):
            # Apply the single use model once
            m.apply()  
        else:
            # This model can be used multiple times, so add it to our new list
            models_multiple_use.append(m)

    models = models_multiple_use  # overwrite models list  


    # Preprocessing: check for all rhs of data sources if they can be aggregated towards the goal rhs
    if  preprocess_rhs:
        # First make right-hand side variables of the start_set correspond to the goal, or terminate when 
        # this is not possible
        start_set_copy = prep_rhs(start_set, goal)
        agg = False  # aggregation was prepared via prep_rhs() so give it zero priority until algorithm is completely stuck
        open_list.append(start_set_copy)  # add start node

        if prints:
            print("Preprocessed starting set of sources into: "+str(start_set_copy))    
    else:
        # No preprocessing of right hand side
        agg = True
        open_list.append(start_set)  # add start node
    
    if prints:
        print("Starting A* search.")
        
    # loop until we find the desired data set
    for i in range(max_iteration):
        if prints:
            print("--- Iteration "+str(i)+" ---")
            print("   Length open list: "+ str(len(open_list)))
            print("   Length closed list: "+ str(len(closed_list)))
           
        if i > 0:
            previous_score = current_score
        
        if len(open_list) == 0:
            # If the open_list is completely empty, the algorithm has failed to find (the next) succesful path.
            # Or all possible paths have been explored (some may have been lost if shedding was enabled).
            
            if find_multiple_paths:
                if len(success_list) > 0:
                    return success_list
            
            end_message = "Open list was empty. Ran for " + str(i) + " iterations."            
            if shedding:
                end_message += " Shedding was used for "+str(shedding_n)+ " best branches. You could try again with more branches or no shedding."
            else: 
                end_message += " No more solutions will be found."

            return end_message
        
        # From all possible neighbours (open_list) for the available set of data sources, take the one with the 
        # highest similarity score
        all_scores = get_scores(similarity_choice, open_list, goal, variant=variant, prints=prints, score_function_parameter=score_function_parameter)
        
        # update current set
        current_index = all_scores.index(max(all_scores))  # find highest scoring index
        current_score = all_scores[current_index]  # update current score
        current_set = open_list[current_index]  # update current set: take the one with highest score
               
        # (optional for speed up) keep only the best options in the open list
        # this speeds up the search, but may lose potential solutions
        if shedding & (len(open_list)>shedding_n):
            top_indices = np.array(all_scores).argsort()[-shedding_n:][::-1]  # find highest scoring indices
            open_list_new = [open_list[i] for i in top_indices]   # take the element with highest score
            open_list = open_list_new

        # pop current set off of the open list and add it to closed list
        try: 
            open_list.remove(current_set) 
        except ValueError: 
            # when shedding, it may occur that the current_set was already removed by the shedding
            pass
        closed_list.append(current_set)
       
        if prints:
            print("   Score of current set: " + str(current_score))
            print("   Scores of previous set: ", previous_score)
            if previous_score >= current_score:
                print("  !! The score was not improved!!")
            print("   Current set: \n" + str(current_set))
            print("   Current set size: " + str(len(current_set.set_of_sources)))
            print("   Path length: " + str(len(current_set.path)))
            print("   Current path: " + str(current_set.path))
          

        if False:
            # check if the goal has been reached
            if (current_set.contains(goal)):
                # A valid path was found
                if find_multiple_paths:
                    # User wants multiple valid paths, so save result and continue
                    success_list.append(current_set)
                else:
                    # User wants a single valid path, so return this path
                    return current_set

        # check if the goal has been reached (by equality), if not check if the goal is reached by shrinking 
        # one of the sources in the current set. If so, this means we need a last step in the path: "contain"
        # This happens in the contains_shrink() function
        goal_found = current_set.contains(goal) or current_set.contains_shrink(goal)
                             
        if goal_found:
            # A valid path was found
            if find_multiple_paths:
                # User wants multiple valid paths, so save result and continue
                success_list.append(current_set)
            else:
                # User wants a single valid path, so return this path
                return current_set
        
        # Identify all neighbours
        n_neighbours_model = 0
        n_neighbours_nonmodel = 0
        
        # Modelling 
        # If modelling is possible, we will try this first (it is usually a good idea to prioritise this)
        # The neighbours found by modelling will be explored in the next step. Later, the non-modelling 
        # neighbours can always be found again.
        all_neighbours_mod, all_path_steps_mod = current_set.get_neighbours_models(
            models=models)  # only modelling
        
        for neighbour, path_step in zip(all_neighbours_mod, all_path_steps_mod):
            # each neighbour of the current set can be created and added to the set
            new_set_tmp = copy.deepcopy(current_set)
            new_set_tmp.add_data_source(neighbour, path_step, i)

            if (new_set_tmp not in open_list) and (new_set_tmp not in closed_list):
                # the new set is not already waiting to be evaluated (open_list) and has also not been 
                # evaluated yet (closed_list)
                open_list.append(new_set_tmp)
                n_neighbours_model += 1
        
        if n_neighbours_model == 0:
            # No models led to new results. So we will now check if combination, aggregation and conversion can be applied
            all_neighbours_reg, all_path_steps_reg = current_set.get_neighbours(agg=agg)  # except modelling (and depending on agg, perhaps also without aggregation)

            if agg==False & len(all_neighbours_reg)==0:
                # if without aggregation there were no neighbours found, we will now try once with aggregation
                all_neighbours_reg, all_path_steps_reg = current_set.get_neighbours(agg=True)  # except modelling

            for neighbour, path_step in zip(all_neighbours_reg, all_path_steps_reg):
   
                # in some cases, models may result in a list of possible outputs
                # we want to add each of these outputs as a separate neighbour
                if isinstance(neighbour, list): 
                    for neighbour_subdata in neighbour:
                        # each neighbour of the current set can be created and added to the set
                        new_set_tmp = copy.deepcopy(current_set)
                        new_set_tmp.add_data_source(neighbour_subdata, path_step, i)

                        if (new_set_tmp not in open_list) and (new_set_tmp not in closed_list):
                            # the new set is not already waiting to be evaluated (open_list) and has also not
                            # been evaluated yet (closed_list)
                            open_list.append(new_set_tmp)
                            n_neighbours_nonmodel += 1
                else:
                    # each neighbour of the current set can be created and added to the set
                    new_set_tmp = copy.deepcopy(current_set)
                    new_set_tmp.add_data_source(neighbour, path_step, i)

                    if (new_set_tmp not in open_list) and (new_set_tmp not in closed_list):
                        # the new set is not already waiting to be evaluated (open_list) and has also not 
                        # been evaluated yet (closed_list)
                        open_list.append(new_set_tmp)
                        n_neighbours_nonmodel += 1
        
        if prints:
            print("   New neighbours: " + str(n_neighbours_model + n_neighbours_nonmodel)
                + " (model: " + str(n_neighbours_model) + ", non-model: "+str(n_neighbours_nonmodel)+")")

    if find_multiple_paths:
        return success_list
    else:
        return {"Did not finish within " + str(max_iteration) + " iterations."}
    

def simulate(n_simulations, start_set, goal, models, max_iteration, similarity_choice = "sum",
          preprocess_rhs = False, shedding=False, shedding_n = 10, variant="base", score_function_parameter=None):
    """Do multiple a* algorithms to get an average mean score"""
    
    t = time.perf_counter()
    times = np.zeros(n_simulations)
    t_start = t
    
    for k in range(n_simulations):
        result = a_star(start_set, goal, models, max_iteration, similarity_choice=similarity_choice, prints=False, 
                        preprocess_rhs = preprocess_rhs, find_multiple_paths=False, shedding=shedding, 
                        shedding_n = shedding_n, variant=variant, score_function_parameter=score_function_parameter) 
        # check if we did not finish
        #if 'Did not finish' in result:
        #    print(f"Couldn't finish one of the simulations in {max_iteration} iterations.")
            
        times[k] = time.perf_counter() - t_start
        t_start = time.perf_counter()

    # if we got through the whole loop
    t_avg = round(np.mean(times),5)
    CI_half_length = round(1.96 * np.std(times, ddof=1) / np.sqrt(n_simulations),10) # ddof=1 to get sample standard deviation (normalize by N-1)
    print(f"Average time to simulate: {t_avg} ± {CI_half_length}.")