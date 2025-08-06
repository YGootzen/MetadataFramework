from metadata_analysis.metadata.data import Data
from metadata_analysis.metadata.path_step import Step
from metadata_analysis.metadata.combining import *

import numpy as np
import itertools as itertools

class SetOfSources:
    """
    Two variants of the similarity score function are implemented: the sum and max of the individual data scores from the data source similarity. 
    """

    def __init__(self, start_set):
        self.set_of_sources = set(start_set)
        self.path = [Step(method="start set")]  # for keeping track of the path that created the current set
        self.tree = []  # for keeping track of which iterations of the algorithm added to this path
        self.score = False 
        
    def __str__(self):
        full_str = "{" + ",\n ".join(sorted([str(d) for d in self.set_of_sources])) + "\n}"
        return full_str
    
    def __eq__(self, other):
        # check if this set equals the other set
        # since the set contains Data objects, which have a __eq__() method, it suffices to rely on that method
        # considered equal if the sets have the same data Data objects, 
        # regardless of order in which the Data objects appear
        return self.set_of_sources == other.set_of_sources
    
    def str_nameonly(self):
        full_str = "{" + ",\n ".join(
                    sorted([d.name for d in self.set_of_sources])) + "\n}"
        return full_str

    def add_data_source(self, data_new: Data, path_step=Step(), iteration="-1"):
        self.set_of_sources = self.set_of_sources.union({data_new})
        self.add_to_path(path_step)
        self.tree.append(iteration)
        self.score = False  # reset score because of change in the set of sources

    def add_to_path(self, path_step: str):
        # For keeping track of the path. 
        # # path_step may be a list of path steps or a single path step. All of them
        # should be added to the path
        if isinstance(path_step, list):
            for ps in path_step:
                self.path.append(ps)
        else:
            self.path.append(path_step)

    def contains(self, data_set: Data):
        """
        Alternative: contains_shrink().
        """

        return any([data_set == d for d in self.set_of_sources])
    
    def contains_shrink(self, other_data_set: Data):
        """
        Similar to contains(), but checks shrink instead of equality
        """    


        # check if any of the data sources in self can be shrinked into other_data_set
        # this takes longer to compute than contain(), so only do this step when other_data_set
        #  is not exactly in self
        # We want to include in the path which dataset we should take the "subset" of.
        
        candidates = []
        for data_in_self in self.set_of_sources:
            if data_in_self.shrink(other_data_set):
                candidates.append(data_in_self)

        
        if len(candidates)>0:
            # At least one data set can be shrinked to other_data_set. Add the goal to the set, and
            # document in the path that this was due to contain/subset/shrink:
            for contained_data in candidates:
                self.add_data_source(other_data_set, path_step=Step(method="subset",
                                                          # join all method details in one line
                                                          method_detail="remove variables or units",
                                                                    input=contained_data,
                                                                    output=other_data_set))
            return True 
        else:
            return False

    def contains_variables_only(self, data_set: Data):
        # Same as contains() except here, we do NOT care about the context 
        # This is used for some models
        
        matching_sources = [
            ds for ds in self.set_of_sources if ds.equal_variables_only(data_set)]
        
        if data_set in self.set_of_sources:
            return matching_sources
        else:
            # check if any of the data sources in self can be shrinked into data_source
            # this takes longer to compute, so only do this step when data_source is not exactly in self
            
            matching_sources = [
                data_in_self for data_in_self in self.set_of_sources if data_in_self.shrink_nocontext(data_set)]
            return matching_sources
        
        
    def data_sources_with_var_left(self, v_name):
        data_sources = set()
        
        for d in self.set_of_sources:
            if d.contains_var_left(v_name):
                data_sources.add(d)
                
        return data_sources
    
    def data_sources_with_var_right(self, v_name):
        data_sources = set()
        
        for d in self.set_of_sources:
            if d.contains_var_right(v_name):
                data_sources.add(d)
                
        return data_sources
            
    def similarity_sum(self, goal_data: Data, variant="base"):
        # only calculate the score if it was not saved from a previous iteration
        if not self.score: 
            self.score = sum((goal_data.similarity(d, variant=variant) for d in self.set_of_sources))
        return self.score
    
    def similarity_topsum(self, goal_data: Data, multiplier=3, variant="base", prints=False):
        # only calculate the score if it was not saved from a previous iteration
        # take the sum of the N highest scores of datasets in the set of sources
        # N is determined by 3*the number of variables of the goal
        # This score function is designed to combat the effect of rewarding a large number of datasources in the 
        # set of sources, which similarity_sum() suffers from. 
        # In exeptional cases, more than three manipulations are needed per variable in the goal set. If you think you 
        # may be in one of these cases, you can gradually increase the multiplier if small values don't succeed.
        if not self.score: 
            all_scores = np.array([d.similarity(goal_data, variant=variant, prints=prints) for d in self.set_of_sources])  # scores per dataset
            n_select = multiplier*(len(goal_data.left_variables) + len(goal_data.right_variables))  # number of variables 
            self.score = all_scores[np.argsort(all_scores)][-n_select:].sum()  # sort scores and sum over N highest
        
        return self.score  
    
    def similarity_max(self, goal_data: Data, variant="base"):

        if not self.score: 
            self.score = max((d.similarity(goal_data, variant=variant) for d in self.set_of_sources)) 
        return self.score 
    
    def similarity_mean(self, goal_data: Data, variant="base"):
        if not self.score: 
            self.score = np.mean(list(d.similarity(goal_data, variant=variant) for d in self.set_of_sources))
        return self.score 

    def similarity_median(self, goal_data: Data, variant="base"):
        if not self.score: 
            self.score = np.median(list(d.similarity(goal_data, variant=variant) for d in self.set_of_sources))
        return self.score 
    
    def similarity_min(self, goal_data: Data, variant="base"):
        if not self.score: 
            self.score = min((d.similarity(goal_data, variant=variant) for d in self.set_of_sources))
        return self.score 
    
    def similarity_minmax(self, goal_data: Data, variant="base"):
        if not self.score: 
            self.score = max((d.similarity(goal_data, variant=variant) for d in self.set_of_sources)) * (min((d.similarity(goal_data, variant=variant) for d in self.set_of_sources)))
        return self.score 
    
    def similarity_maxmean(self, goal_data: Data, variant="base"):
        if not self.score: 
            self.score = max((d.similarity(goal_data, variant=variant) for d in self.set_of_sources)) + np.mean(list(d.similarity(goal_data, variant=variant) for d in self.set_of_sources))
        return self.score 
        
    def similarity_maxmeanmin(self, goal_data: Data, variant="base"):
        if not self.score: 
            self.score = max((d.similarity(goal_data, variant=variant) for d in self.set_of_sources)) * np.mean(list(d.similarity(goal_data, variant=variant) for d in self.set_of_sources)) * min((goal_data.similarity(d, variant=variant) for d in self.set_of_sources))
        return self.score 
    
    def similarity_max_per_variable(self, goal_data: Data, variant="base"):  
        if not self.score: 
            idx = 0
        
            goal_contexts = goal_data.context
            maxs = np.zeros(len(goal_data.left_variables)*len(goal_contexts))
            
            for context in goal_contexts:
                
                for var in goal_data.left_variables:
                    data_sources = self.data_sources_with_var_left(var.name)
                    
                    if data_sources:
                        maxs[idx] = max((d.similarity(goal_data, variant=variant) for d in data_sources if context in d.context))
                    idx += 1
                
            self.score = np.mean(maxs)
        return self.score    
    
    def similarity_max_per_variable_bonus(self, goal_data: Data, variant="base"):
        # Reimplemented from the students' version, disregarding context for now
        
        if not self.score: 
            idx = 0
        
            maxs = np.zeros(len(goal_data.left_variables))
            maxs_data_sources = []
            
            for left_var in goal_data.left_variables:
                # get all data sources in current_set that have the same left variable
                data_sources_left_match = list(self.data_sources_with_var_left(left_var.name))

                if len(data_sources_left_match) > 0:
                    # one or more data sources were found
                    
                    scores_list = [d.similarity(goal_data, variant=variant) for d in data_sources_left_match]
                    max_idx = np.argmax(scores_list)
                    max_data_source = data_sources_left_match[max_idx]
                    maxs_data_sources.append(max_data_source.right_variables)
                    maxs[idx] = scores_list[max_idx]
                idx += 1
                    
            bonus_mult = len(set.intersection(*maxs_data_sources)) / len(set.union(*maxs_data_sources))
            
            self.score = np.mean(maxs) * (bonus_mult + 1)/2    # don't start at 0
        return self.score 
                        
    def get_neighbours(self, agg = True):
        # based on conversion, aggregation and combination, give all unique datasets that can be created from the current set, with exactly one manipulation
        # returns a set of tuples containing (Data, Step) objects
        
        all_neighbours = []  # Initialise set where we'll store all neighbours found
        all_path_steps = []

        # Conversion and aggregating
        for d in self.set_of_sources:
            # add all items in the set d.get_neighbours() to all_neighbours
            # These neighbours come from the individual datasets (and already have their path noted). 
            neighbours, path_steps = d.get_neighbours(agg)

            # Only add the model output data if it is not yet included in neighbours:
            for i in range(len(neighbours)):
                if neighbours[i] not in all_neighbours:
                    all_neighbours.append(neighbours[i])
                    all_path_steps.append(path_steps[i])
        
        # Combination
        set_of_sources_temp = list(self.set_of_sources)  # temporarily make the set of sources into a list, so the indices are fixed
        
        for i, j in zip(*np.triu_indices(len(set_of_sources_temp), k=1)):
            # Loop through all combinations of (two) available data sources by using the indices of the upper 
            # triangle without diagonal (offset k=1) of a matrix of size n by n, where n = len(self.set_of_sources)
        
            combines_temp_row, combines_temp_col = combines(set_of_sources_temp[i], set_of_sources_temp[j])
            if combines_temp_row:
                # Rowwise combination was possible, so add result to neighbours
                combines_temp_row.path_step = Step("combine", "rowwise", "", str(combines_temp_row))
                all_neighbours.append(combines_temp_row)  
                
            if combines_temp_col:
                # Columnwise combination was possible, so add result to neighbours
                combines_temp_col.path_step = Step("combine", "columnwise", "", str(combines_temp_col))
                all_neighbours.append(combines_temp_col) 
                        
        return all_neighbours, all_path_steps
    

    def get_neighbours_models(self, models=None):
        # based on modelling, give all unique datasets that can be created from the current set, with exactly one modelling manipulation
        # this will not return any neighbours that can be created through conversion, aggregation or combination

        # returns a set of tuples containing (Data, Step) objects

        if models is None:
            return None
        
        all_neighbours = []  # Initialise list where we'll store all neighbours found
        all_path_steps = []

        for model_tmp in models:
            # determine number of input data sets required for model_tmp
            n_input = len(model_tmp.input_data)

            # create a list of all possible combinations of the required number of input data sets
            input_combinations = list(itertools.combinations(self.set_of_sources, n_input))

            for dataset_selection in input_combinations:

                if model_output := model_tmp.apply(potential_input=list(dataset_selection)):
                    # The model was applicable and returned output. Add this output to the set of all neighbours.
                    # When unapplicable the value of model_output is False, and no neighbour will be added.
                    for mo in model_output:
                        # Update the paths for eachs of the output data sets
                        path_step_tmp = Step("model", model_tmp.name, model_tmp.input_data, mo)
                        # all_neighbours.update([(model_output, path_step_tmp)])  # Update all_neighbours
                        # Update all_neighbours
                       
                        # ideally, neighbours would be a set (but we need a fixed order to know which
                        # path steps are matched). Only add the model output data if it is not yet
                        # included in neighbours:

                        if mo not in all_neighbours:
                            all_neighbours.append(mo)
                            all_path_steps.append(path_step_tmp)

        return all_neighbours, all_path_steps
