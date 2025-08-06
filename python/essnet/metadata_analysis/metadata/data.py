
"""
A data set consists of a set of left-hand variables, a set of right-hand variables and a set if included units. 
The similarity() method is used in the SetOfSources class, where the individual similarity scores of each data 
set are combined into a single value.
"""

import copy as copy
from typing import Union

from metadata_analysis.metadata.aggregation import AggregationGraph
from metadata_analysis.metadata.conversion import ConversionGraph
from metadata_analysis.metadata.variable import Variable
from metadata_analysis.metadata.set_of_included_units import SetOfIncludedUnits, SetOfIncludedUnitsUnion
from metadata_analysis.metadata.path_step import Step

class Data(object):
    def __init__(self, left_variables, right_variables, set_of_units: Union['SetOfIncludedUnits', 'SetOfIncludedUnitsUnion'], 
                 name="", description=""):
        self.left_variables = set(left_variables)  # measurement variables
        self.right_variables = set(right_variables)  # identifier variables
        self.set_of_units = set_of_units
        self.score = False 
        self.name = name  # string: for printing a path that's easy to understand
        self.description = description  # string: a longer description that indicates the variables included in the data set
        
    def __str__(self):
        full_str = self.name + " " + self.str_notation()
        return full_str
    
    def __eq__(self, other: "Data"):
        # compare self Data object to the other Data object
        # they are equal if all left- and right- sets of variables, and the set of included units, are equal
        
        # use all for efficient evaluation (stops at the first element that is False)
        return all([self.left_variables == other.left_variables,
                    self.right_variables == other.right_variables,
                    self.set_of_units == other.set_of_units])
    
    def __hash__(self):
        # required for usage in sets. Since the str() of self is unique and contains all elements for equality, we use this for the hash.
        # This does not rely on the name, which is user specified and may accidentaly be added twice.
        left_str_separate = [str(v) for v in self.left_variables]
        left_str_separate.sort()
        left_str = ", ".join(left_str_separate)
        right_str_separate = [str(v) for v in self.right_variables]
        right_str_separate.sort()
        right_str = ", ".join(right_str_separate)
        
        str_no_name = " (" + left_str + " | " + right_str + ")" + self.set_of_units.name

        return hash(str(str_no_name))
    
    def str_notation(self):
        left_str_separate = [str(v) for v in self.left_variables]
        left_str_separate.sort()
        left_str = ", ".join(left_str_separate)
        right_str_separate = [str(v) for v in self.right_variables]
        right_str_separate.sort()
        right_str = ", ".join(right_str_separate)
        notation = "(" + left_str + " | " + right_str + ")" + "_" + self.set_of_units.name
        return notation
    
    def str_descriptive(self, legend_variables=None):
        """
        Return a word-based description of the data set.
        """
        if legend_variables is None:
            # assumes the variable names and granularities are already words
            left_str_separate = [str(v) for v in self.left_variables]
            left_str_separate.sort()
            left_str = ", ".join(left_str_separate)
            right_str_separate = [str(v) for v in self.right_variables]
            right_str_separate.sort()
            right_str = ", ".join(right_str_separate)
            full_str = self.name + \
                ": " + left_str + " per " + right_str + "." + \
                " For set of included units " + self.set_of_units.name
        else: 
            # legend_variables is available, use it to look up the descriptive terms 
            intro = str(self)+ ": \n   "
            left_str_separate = [legend_variables[v.name]["name"]+"["+  # look up variable descriptive name
                                 str(legend_variables[v.name]["granularities"][v.granularity])+"]" # look up granularity descriptive
                                 for v in self.left_variables]
            left_str_separate.sort()
            left_str = ", ".join(left_str_separate)
            right_str_separate = [legend_variables[v.name]["name"]+"[" +  # look up variable descriptive name
                                  # look up granularity descriptive
                                  str(legend_variables[v.name]
                                      ["granularities"][v.granularity])+"]"
                                  for v in self.right_variables]
            right_str_separate.sort()
            right_str = ", ".join(right_str_separate)
            full_str = intro + left_str + " \n   per \n   " + right_str + \
                " \n   for set of included units " + self.set_of_units.name+"."

        return full_str

    def equal_variables_only(self, other: "Data"): 
        # compare self Data object to the other Data object
        # similar to __eq__() except that this function does not care about set of included units
        # they are considered equal if all left- and right- sets of variables, are equal
        
        # use all for efficient evaluation (stops at the first element that is False)
        return all([self.left_variables == other.left_variables,
                    self.right_variables == other.right_variables])
        
    def get_variable_names_left(self):
        return {v.name for v in self.left_variables}
    
    def contains_var_left(self, v_name):
        return v_name in self.get_variable_names_left()
        
    def get_variable_names_right(self):    
        return {v.name for v in self.right_variables}
    
    def contains_var_right(self, v_name):
        return v_name in self.get_variable_names_right()
        
    def reset_score(self):
        # Always make sure to reset the score when making a (deep) copy of a dataset, or if you adjust any variables
        self.score = False

    def convert_variable(self, var_remove, var_add):
        if var_remove.name != var_add.name:
            # we can only convert within the same variable
            # only the granularities may be different
            return None
        # create a copy of self as "input" for this conversion step
        self_input = copy.deepcopy(self)

        # beware: the check if this conversion is allowed should be executed before this method is used
        self.left_variables.remove(var_remove)
        self.left_variables.add(var_add)

        # document the change in the dataset in it's name and path
        # * denotes: some change was made to the original data set
        self.name = self.name + "*"
        # look up if the conversion was the result of a model
        # look up conversion graph
        conversion_graph = ConversionGraph.get(var_remove.name)
        # check if edge was result of a model
        method_name, method_detail = conversion_graph.get_path_detail(
            var_remove.granularity, var_add.granularity)

        path_step = Step(method=method_name,
                         method_detail=method_detail,
                         input=str(self_input),
                         output=str(self))
        self.score = False

        return path_step


        
    def aggregate_variable(self, var_remove, var_add):
        if var_remove.name != var_add.name:
            # we can only aggregate within the same variable
            # only the granularities may be different
            return None
        # create a copy of self as "input" for this aggregation step 
        self_input = copy.deepcopy(self)

        # beware: the check if this aggregation is allowed should be executed before this method is used
        self.right_variables.remove(var_remove)
        self.right_variables.add(var_add)

        # document the change in the dataset in it's name and path
        # * denotes: some change was made to the original data set
        self.name = self.name + "*"
        # look up if the aggregation was the result of a model
        # look up aggregation graph
        aggregation_graph = AggregationGraph.get(var_remove.name)
        # check if edge was result of a model

        method_name, method_detail = aggregation_graph.get_path_detail(var_remove.granularity, var_add.granularity)

        path_step = Step(method=method_name,
                         method_detail=method_detail,
                         input=str(self_input),
                         output=str(self))
        self.score = False

        return path_step
    
    def similarity(self, other: "Data", variant = "base", prints=False,
                   weight_right_sim = 1, weight_right_eq = 5, weight_left_sim = 2, weight_left_eq = 5,
                   weight_units = 5):
        # other is the goal Data
        
        if not self.score: # only calculate the score if it is not known yet

            n_goal_vars_left = len(self.left_variables)
                
            left_equal = len(set(self.left_variables).intersection(other.left_variables))  # number of variables with equal name and granularity
            right_equal = len(set(self.right_variables).intersection(other.right_variables))  # number of variables with equal name and granularity
            
            left_similar = len(self.get_variable_names_left().intersection(other.get_variable_names_left()))  # number of variables with equal name (those with equal granularity are counted again, so keep this in mind when setting weights)
            left_similar -= left_equal    # remove double-counting
            right_similar = len(self.get_variable_names_right().intersection(other.get_variable_names_right()))  # number of variables with equal name (those with equal granularity are counted again, so keep this in mind when setting weights)
            right_similar -= right_equal  # remove double-counting
        
            units_score = weight_units*(self.set_of_units == other.set_of_units)
            
            left_equal_max = len(set(other.left_variables))  # number of variables with equal name and granularity
            right_equal_max = len(set(other.right_variables))  # number of variables with equal name and granularity

            base_score = sum([weight_left_eq*left_equal, weight_left_sim*left_similar,
                            weight_right_eq*right_equal, weight_right_sim*right_similar,
                            units_score])
            
            
            if variant == "base":
                # simply sum the multiplications of the variable weights
                self.score = base_score
            elif variant == "base_coupled":
                # simply sum the multiplications of the variable weights
                self.score = (sum([weight_left_eq*left_equal, weight_left_sim*left_similar]) *
                        sum([weight_right_eq*right_equal, weight_right_sim*right_similar, units_score]))
            elif variant == "individual":
                # named "likeness" in the paper
                # this may be a little slower because of the for loop, but it will keep the algorithm from adding unneccesary variables to datasets
                # This similarity function is assymetric. It assumes that other is the goal and self is a dataset from one of the stages in the algorithm

                score_tmp = 0  # Initialize score

                # left hand side                    
                for goal_v_l in other.left_variables:
                    if goal_v_l in self.left_variables: 
                        # an exact match on granularity is present
                        score_tmp += weight_left_eq

                    elif goal_v_l.name in self.get_variable_names_left():
                        # similar match on variable name (wihtout granularity)
                        score_tmp += weight_left_sim

                # right hand side
                for goal_v_r in other.right_variables:
                    if goal_v_r in self.right_variables: 
                        # an exact match on granularity is present
                        score_tmp += weight_right_eq

                    elif goal_v_r.name in self.get_variable_names_right():
                        # similar match on variable name  (wihtout granularity)
                        score_tmp += weight_right_sim

                if other.set_of_units == self.set_of_units:
                    score_tmp += units_score

                # penalize sources that have more variables in them 
                score_tmp = score_tmp / (len(set(self.left_variables)) + len(set(self.right_variables)))
                self.score = score_tmp

            elif variant == "normalized":   # this is the default
                # normalize score:
                # by dividing by the maximum score that could be acchieved based on the number of variables in this source
                # large sources gain a higher penalty
                self.score = base_score / sum([weight_left_eq * left_equal_max, weight_right_eq * right_equal_max, weight_units])
            
            elif variant == "normalized_coupled":
                # normalize score, but with rhs and lhs dependently (multiply instead of sum)
                self.score = ((sum([weight_left_eq*left_equal, weight_left_sim*left_similar]) *
                        sum([weight_right_eq*right_equal, weight_right_sim*right_similar, units_score])) /  
                        (weight_left_eq * left_equal_max * (weight_right_eq * right_equal_max + weight_units)))
            if prints: 
                print("   Score for a new data set: "+str(self)+" and other (goal): "+str(other)+ ". Score: "+str(self.score))

        return self.score
    
    def get_neighbours(self, agg = True):
        # based on conversion and aggregation, give all unique datasets that can be created from datasource self, with exactly one manipulation
        
        # conversion
        neighbours = []
        path_steps = []
        for v in self.left_variables:
            # for each of the left variables, it can be converted to one of its connected granularities in the conversion graph
            conversion_graph = ConversionGraph.get(v.name)
            connected_granularities = conversion_graph.all_conversions(v.granularity)
            for g in connected_granularities:
                v2 = Variable(name=v.name, granularity = g)  # copy the name, but use new granularity
                data_temp = copy.deepcopy(self)  # copy of the current data set
                # * denotes: some change was made to the original data set
                data_temp.name = self.name + "*"
                path_step_tmp = data_temp.convert_variable(var_remove = v, var_add = v2)  # apply conversion (we have checked that it is valid when creating connected_granularities)
                neighbours.append(data_temp)
                path_steps.append(path_step_tmp)
        
        # aggregation 
        if agg:
            for v in self.right_variables:
                # for each of the left variables, it can be converted to one of its connected granularities in the conversion graph
                aggregation_graph = AggregationGraph.get(v.name)
                connected_granularities = aggregation_graph.all_aggregations(v.granularity)

                for g in connected_granularities:
                    v2 = Variable(name=v.name, granularity = g)  # copy the name, but use new granularity
                    data_temp = copy.deepcopy(self)
                    path_step_tmp = data_temp.aggregate_variable(var_remove=v, var_add=v2)
                    neighbours.append(data_temp)
                    path_steps.append(path_step_tmp)
                    
        # combination is not relevant when looking at a single data source, because two sources are always required for combining
        
        return neighbours, path_steps
    
    def shrink(self, other: "Data"): 
        """
        Returns True if self can be 'shrinked' into other. 

        Solution to a combination issue where:

        (a1, b3 | a3, c1)_I  +  (b2, e1 | a3, c1)_I  ->  (a1, b2, b3, e1 | a3, c1)_I

        results in both b2 and b3 being in the dataset. The shrink() function checks if a data set (self) is 
        within data set other. Returns true/false. This is also relevant to the case:

        (a1, b3 | a3, c1)_I  +  (b3, e1 | a3, c1)_I  ->  (a1, b3, e1 | a3, c1)_I

        where the goal is a subset of the result of combining, such as (a1, e1 | a3, c1)_I.

        Left-hand variables can be dropped at any time without messing up the structure of the data set.

        Dropping right-hand variables is a current point of discussion.  
        -   Right-hand variables can not simply be dropped. If dropped, duplicate units might exist in the 
        dataset because part of the unit descriptor is suddenly missing. Because of this, the sets of 
        right-hand variables must be equal. 
        -   For now, we will drop right hand variables, but know that this may be an issue for future
        cases and we will reconsider then.
        """

        # If right variables cannot be dropped:
        #return all([other.left_variables.issubset(self.left_variables),
        #            self.right_variables == other.right_variables,
        #            other.set_of_units.is_subset(self.set_of_units)]) 

        # If right variables can be dropped:
        return all([other.left_variables.issubset(self.left_variables),
                    other.right_variables.issubset(self.right_variables),
                    other.set_of_units.is_subset(self.set_of_units)])
    
    def shrink_variables_only(self, other: "Data"):
        """
        Returns True if self can be 'shrinked' into other, based on variables only. 
        See Data.shrink() for an explanation on the ideas behind shrinking. 
        Similarly to equal_variables_only(), we disregard the sets of included units.
        """

        # If right variables cannot be dropped:
        # return all([other.left_variables.issubset(self.left_variables),
        #            self.right_variables == other.right_variables)])

        # If right variables can be dropped:
        return all([other.left_variables.issubset(self.left_variables),
                    other.right_variables.issubset(self.right_variables)])
