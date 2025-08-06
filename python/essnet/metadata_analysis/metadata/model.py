import itertools
import copy 
import warnings

class Model:
    """
    Modelling is currently implemented as exceptions to the rules of the other manipulations. Each available model, however trivial, 
    must be specified. A model is based on a set of input data and output data. If the input data is available, then the output data 
    can be acchieved. 
    """
    def __init__(self, input_data, output_data, units_rule):
        self.input_data = set(input_data)  # can be multiple data sources
        self.output_data = output_data
        self.units_rule = units_rule
        self.name = "Unnamed"

    def __str__(self):
        input_str = " + ".join([str(x) for x in self.input_data])
    
        return self.name + ": " + input_str + " -> " + str(self.output_data)
            
    def apply(self, potential_input):
        # Note: many set of included units rules can be thought of. If they get so specific that the relation between sources and 
        # set of included units matter, 
        # the intention is to write a child class that overwrites the apply() function for the specific case
            
        # If each source in the required input (self.input_data) is present in the potential_input, then the model is applicable
        # It gets a bit tricky to check this, because sometimes, the set of included units is less strictly required then other times, leading 
        # to multiple sources the model is applicable to
        
        if self.units_rule == "exact":
            # Check if the all input sources are available in the potential input, with exact matches for set of included units
            
            if all([input_source in potential_input for input_source in self.input_data]):
                # based on exact matches
                return [self.output_data]
            else:
                # if for all required data sources, there is a source in the potential data that can be shrinked into the required data source, 
                # the model can also be applied
                results = []
                for required_data in self.input_data:
                    results.append(any([ds.shrink(required_data) for ds in potential_input]))
                    
                # check if shrinking was enough to satisfy requirements
                if all(results):
                    return [self.output_data]
                else:
                    return False
        
        elif self.units_rule in ["intersection", "union", "equal"]:
            # For these units_rule's we'll need to do some set manipulation to find out if the model requirements are met
            
            output_list = []  # here we will add any outcomes for the inputs that satisfy the set of included units requirements
            units_matches = []  # list of lists 
            
            for input_data_temp in self.input_data:
                # For each required input_data source, check if there are matches in potential_input. If so, add their set of 
                # included units to the list. Use Data.shrink_variables_only() because we are content if the required
                # input data is a subset of available data. 
                units_matches_temp = [ds.set_of_units for ds in potential_input if ds.shrink_variables_only(input_data_temp)]
                units_matches.append(units_matches_temp)
            
            if all(len(units_matches_temp)>0 for units_matches_temp in units_matches):
                # For all required input sources, at least one available data source was found
                
                for units_permutation in itertools.product(*units_matches):
                    # Note: * unpacks the list units_matches once. This results in units_permutations being a tuple of the same length
                    # as the number of required input sources.
                    
                    if self.units_rule == "intersection":
                        # The set of included units of the output_data is the intersection of all sets of units of the input data. 
                        # If no intersection is possible, the model cannot be applied
            
                        units_new = units_permutation[0] 

                        # The intersection method works only on two sets of units at a time, so we'll have to loop over the 
                        # sets of units that need to be a part of the intersection

                        for soiu in units_permutation[1:]:
                            units_new = units_new.intersection(soiu)

                            if not units_new:
                                # If intersection was not possible (due to different unit types for example)
                                # or if the intersection was empty, result wil be False
                                # In that case, the model cannot be applied for this permuation of unit matches
                                break
                        # If this resulted in a non-empty set of units, we have found a permutation that can be applied! 
                            
                    elif self.units_rule == "union":
                        # The set of included units of the output_data is the union of all sets of units of the input data. 
                        # If no union is possible, the model cannot be applied
            
                        units_new = units_permutation[0] 

                        # The union method works only on two sets of units at a time, so we'll have to loop over the 
                        # sets of units that need to be a part of the union

                        for soiu in units_permutation[1:]:
                            units_new = units_new.union(soiu)

                            if not units_new:
                                # If union was not possible (due to different unit types for example)
                                # or if the union was empty, result wil be False
                                # In that case, the model cannot be applied for this permuation of unit matches
                                break
                        # If this resulted in a non-empty set of units, we have found a permutation that can be applied! 
                        
                            
                    elif self.units_rule == "equal":
                        # The set of included units of the output_data is equal to all sets of included units, 
                        # if they are all equal
            
                        if len(set(units_permutation)) > 1:
                            # not all sets of units were equal
                            units_new = False
                        else:
                            # Since they are all equal, we can simply take the first one
                            units_new = units_permutation[0] 
        
                    if units_new:
                        # Now, we can generate an output of the model.
                        output_data_temp = copy.deepcopy(self.output_data)  # copy the output_data
                        output_data_temp.set_of_units = units_new  # overwrite the set of included units
                        output_list.append(output_data_temp)  # add to model output

                if len(output_list) > 0:
                    # One ore more results were found, these can now be returned
                    return set(output_list)
            else:
                return False
                 
        else: 
            warnings.warn("Modelling: the rules regarding the set of included units were not clear for: "+self.name)
            return False
        

class ModelSingleUse(object):
    """
    Single use models are intended to be applied once, before the path search starts. One example
    of a single use model is adding an aggregation edge that is usually not available (from a high
    granularity value to a low granularity value for example).
    """

    def __init__(self):
        self.name = "Unnamed"

    def __str__(self):
        return str(self.name)

    def apply(self):
        """
        Write custom code for application of the model here. Return True if the model was applied 
        succesfully. Return False if the model cannot be applied, so this may be relayed to the user.
        """
        return True