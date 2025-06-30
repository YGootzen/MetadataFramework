"""
Describes which units are included in a dataset. The first part of the description is the variable that defines the unit type
 (e.g. persons, businesses, road segments, cars). The second part of the description is based on variables with a constant 
 value (e.g. country = The Netherlands, year = 2025). These variables are defined with the `VariableSpec` class. It's also 
 possible a set of values is present (e.g. year $in {2024, 2025}$). The definitions of set of included units is chosen 
 such that set theory may be applied. A crucial step is to check if all values for a variable are complete, in that case, 
 the variable may be removed from the description of set of included units.
"""

import copy as copy
from typing import Union
from itertools import product

from metadata_analysis.metadata.errors import BadUnionError
from metadata_analysis.metadata.variable import Variable
from metadata_analysis.metadata.variable_spec import VariableSpec
from metadata_analysis.metadata.aggregation import AggregationGraph, AggregationTable

class SetOfIncludedUnits:
    def __init__(self, name, unit_type_var: 'Variable' = Variable(), specifying_variables={}):
        self.name = name  # for printing
        self.unit_type_var = unit_type_var

        self.specifying_variables = set(specifying_variables)  # set of specifying_variables
    

    def __str__(self):
        # create a list of the specifying variables 
        specvar = sorted([str(vv) for vv in list(self.specifying_variables)])
        specvar_str = ", ".join(specvar)

        # paste everything together
        selfstr = str(self.name) + ": {" +str(self.unit_type_var) + " -- " + specvar_str + "}"
        
        return selfstr
    

    def __hash__(self):
        return(hash(str(self)))
    

    def __eq__(self, other: 'SetOfIncludedUnits'):
        # Returns True if self and other contain the same units, False otherwise
        # The is_subset() method returns True if a subset or equal, so if this
        # is true in both directions, than the two sets must be equals.

        return self.is_subset(other) and other.is_subset(self)
    
        
    def is_subset(self, other: ['SetOfIncludedUnits', 'SetOfIncludedUnitsUnion']):
        """
        Check wether the self SOIU is a subset of the (potentially larger) other SOIU
        """
        # 1) for the two sets to be comparable, they must be defined on the same unit type
        if self.unit_type_var != other.unit_type_var:
            return False
        
        # Redirect if SetOfIncludedUnitsUnion
        if isinstance(other, SetOfIncludedUnitsUnion):
            # The class SetOfIncludedUnitsUnion has a method SetOfIncludedUnitsUnion.is_subset()
            # that we will refer to, since other is SetOfIncludedUnitsUnion.
            # The method is not symmetrical, so we will make a SetOfIncludedUnitsUnion version
            # of self (that is currently SetOfIncludedUnits, otherwise we would not be here)

            self_version = SetOfIncludedUnitsUnion(set_of_soiu = [self])
            
            return self_version.is_subset(other)
        
        # 2) all of the specying variables and their values must be a subset of the specifying values in the otherSOIU  
        # Preparation to check later if all s.var from other are in self
        other_all_specvars = copy.deepcopy(other.specifying_variables)  

        for spec_var_self in self.specifying_variables:
            # For every specifying variable in self, there must be either 
            
            # Try to retrieve the specifying variable from other:
            if spec_var_other := other.get_specifying_variable(specvar_name=spec_var_self.name):
                other_all_specvars.remove(spec_var_other)  # this specvar from other has been checked

                # Other contains this specifying variable, so we must check if spec_var(from self) is a subset 
                # of the specifying variable of other
                if not spec_var_self.is_subset(spec_var_other):
                      # There is no specifying variable in other of which the specifying variable from is a subset.
                    # We need this for all spec_var_self, so we can stop searching and return False.
                    return False
            
            # Other does not contain the specifying variable spec_var_self, hence containing all possible 
            # values for that variable. So other is the larger set and self may still be a subset of other.

        if len(other_all_specvars) > 0:
            # Other contains at least one specifying variable that self does not contain. 
            # Therefore, some units of self are not contained in other, and self is not a subset of other.
            return False

        # Now all constraints set by self's specifying variables have been met.
        # We also need to check if other doesn't have any specifying variables left that are not a part of self.

        # We made it out of the loop, so we know all specifying variables are a subset of other.    
        return True
    

    def intersection(self, other: ['SetOfIncludedUnits', 'SetOfIncludedUnitsUnion']):
        # Returns the union of the two sets of included units self and other, if this can be determined.
        # The returned object is again a SetOfIncludedUnits. We need to determine the name, unit_type_var, 
        # and specifying_variables

        # Check wether the self SOIU is a subset of the (potentially larger) other SOIU
        if isinstance(other, SetOfIncludedUnitsUnion):
            # The class SetOfIncludedUnitsUnion has a method SetOfIncludedUnitsUnion.intersection()
            # that we will refer to, since other is SetOfIncludedUnitsUnion and the method is symmetrical.
            # Self will now become "other", which is allowed to be SetOfIncludedUnits.
            return other.intersection(self)

        if self == other:
            # the intersection has no effect
            return self
        
        if self.is_subset(other):
            # self is completely within other, so the intersection is described by self
            return self
        
        if other.is_subset(self):
            # other is completely within self, so the intersection is described by other
            return other

        # First, for the two sets to be intersected, they must be defined on the same unit type
        if self.unit_type_var != other.unit_type_var:
            return False
        # They have the same unit_type_var, so this is also the unit type of the resulting set
        result_unit_type_var = self.unit_type_var

        # The name of the resulting SetOfIncludedUnits is the two original names with a "union" in between
        # Sort the names to create uniformity in the new name (because the intersection is symmetrical)
        names = [self.name, other.name]
        names.sort()
        result_name = " \u2229 ".join(names)

        result_specifying_vars = set()

        # For every specifying variable in both sets, check if it also occurs in the other set, and 
        # put the variable (potentially intersected with the other set) in the resulting variables
        # Exact duplicates of variables (and their available values) from both sets will be contained
        # only once in spec_vars_to_check, because of __eq__() of specifying variables. 
        spec_vars_to_check = self.specifying_variables.union(other.specifying_variables)

        while spec_vars_to_check:
            # until spec_vars_to_check is empty, analyse the variables inside
            spec_var_intersect = spec_vars_to_check.pop()  # get a specifying variable from the set at random 
            # See if there are other variables with the same name in the set
            similar_spec_var = {sv for sv in spec_vars_to_check if sv.name == spec_var_intersect.name}

            for spec_var_other in similar_spec_var:
                # create intersection with each variable with a similar name
                # then update spec_var_intersect with the intersection
                spec_var_intersect = spec_var_intersect.intersection(spec_var_other)
            
                # Remove spec_var_other from the list of variables to check, because we have seen it now
                spec_vars_to_check.remove(spec_var_other)
                
                if not bool(spec_var_intersect.value_available):
                    # The available set of values for this specifying variable is empty 
                    # (likely due to the intersection)
                    # This means no units remain in the resulting set of units and we don't have to 
                    # calculate the intersections for the other specifying variables
                    return False

            result_specifying_vars.add(spec_var_intersect)
        
        return SetOfIncludedUnits(name = result_name, 
                                  unit_type_var = result_unit_type_var, 
                                  specifying_variables = result_specifying_vars)


    def union(self, other: ['SetOfIncludedUnits', 'SetOfIncludedUnitsUnion']):
        # Returns the union of the two sets of included units self and other, if this can be determined.
        
        # Check wether the self SOIU is a subset of the (potentially larger) other SOIU
        if isinstance(other, SetOfIncludedUnitsUnion):
            # The class SetOfIncludedUnitsUnion has a method SetOfIncludedUnitsUnion.union()
            # that we will refer to, since other is SetOfIncludedUnitsUnion and the method is symmetrical.
            # Self will now become "other", which is allowed to be SetOfIncludedUnits.
            return other.union(self)

        # Check a few simple cases, that result in the answer being self or other
        if self == other:
            # the union has no effect
            return self
        
        if self.is_subset(other):
            # self is already within other, so the union is described by other
            return other
        
        if other.is_subset(self):
            # other is already within self, so the union is described by self
            return self

        # For the two sets to be joined together, they must be defined on the same unit type
        if self.unit_type_var != other.unit_type_var:
            return False
        
        # They have the same unit_type_var, so this is also the unit type of the resulting set
        result_unit_type_var = self.unit_type_var

        # The name of the resulting SetOfIncludedUnits is the two original names with a "union" in between
        # Sort the names to create uniformity in the new name (because the intersection is symmetrical)
        #names = [self.name, other.name]
        #names.sort()
        #result_name = " \u222a ".join(names)
        #result_specifying_vars = set()
        
        # In some cases, the union of the two sets may be defined nicely by a "cleanly written"
        # set of included units. An example of such a case is when all variables are specified on the same granularity
        # and the two sets only differ on the value of one variable. 

        # In many other cases, the union of two sets of included units cannot be written nicely. This happens
        # when the two sets have a non-rectangular shape when drawn (see notes from 23-05-2025).

        # For now, we'll simply reference to a union() as a set of included units, defined
        # by two other sets of inlcuded units. 

        return SetOfIncludedUnitsUnion([self, other])


    def get_specifying_variable(self, specvar_name):
        """
        Returns the specifying variable corresponding with name specvar_name.
        """

        for specvar_tmp in self.specifying_variables:
            if specvar_tmp.name == specvar_name:
                return specvar_tmp
        return False


    def adjust_granularities(self, desired_granularities):
        """
        Adjust the granularities of the specifying variables and their values using the aggregation table. 
        There must be a path from the current granularity to the desired granularity.
        If one of the variables described by desired_granularities is not present in the soiu, then it must
        have been complete, so add all available values.
        """

        self_new = copy.deepcopy(self)
        for specvar_desired_name, specvar_desired_gran in desired_granularities.items():
            # Make an adjustment, if needed, for evey specified variable

            if specvar := self.get_specifying_variable(specvar_name=specvar_desired_name):
                # The variable is used in the specifying variables of this soiu. We can call it using specvar.
                if not specvar.granularity == specvar_desired_gran:
                    # The granularity does not match the desired granularity: adjustment needed.
                    agg_graph = AggregationGraph.get(specvar_desired_name)  # get relevant aggregation graph
            
                    if agg_table := agg_graph.get_aggregation_table(granularity_from = specvar_desired_gran,  # and the relevant table
                                                                granularity_to=specvar.granularity):
                        
                        # Add as a specifying variable, with all available values
                        specvar_to_add = VariableSpec(name = specvar_desired_name, 
                                                    granularity = specvar_desired_gran,
                                                    value_available = agg_table.get_translated_variables(specvar.value_available))  # look up all translated values in the desired granularity
                        
                        # Remove current specvar and add adjusted version
                        self_new.specifying_variables.remove(specvar) 
                        self_new.specifying_variables.add(specvar_to_add)
                    
                # Else: This variables is already at the desired granularity, no need for adjustments.
            else:  
                # This variable not present in the soiu, so it must have been complete. Add all available values.
                agg_graph = AggregationGraph.get(specvar_desired_name)  # get relevant aggregation graph
                if agg_table := agg_graph.get_aggregation_table(granularity_from = specvar.granularity,  # and the relevant table
                                                            granularity_to = specvar_desired_gran):
                    # Add as a specifying variable, with all available values
                    specvar_to_add = VariableSpec(name = specvar_desired_name, 
                                                granularity = specvar_desired_gran, 
                                                value_available = agg_table.get_all_values(self, specvar_desired_gran))  # look up all possible values in the desired granularity
                
                    self_new.specifying_variables.add(specvar_to_add)
        return self_new
    
    
    def split(self):
        """
        Returns a list of soiu's, with one soiu or every combination of specifying values granularities. 
        Based on a list of SetOfIncludedUnits objects, each with a single value
        per specifying variable, collectively covering all the values in the original.
        """
        # Extract the value sets from each specifying variable
        value_sets = [var.value_available for var in self.specifying_variables]

        # Generate all combinations
        combinations = product(*value_sets)

        # Create a new SetOfIncludedUnits for each combination
        soiu_subsets = []  # for consequent naming of the subset soiu's
        subset_number = 0
        for combo in combinations:
            # Create a list of specifying variables, each with one value
            new_vars = [VariableSpec(name=var.name,
                                    value_available={value},  # single value
                                    granularity=var.granularity)  # assuming granularity is present
                                for var, value in zip(self.specifying_variables, combo)]

            # Create a new SetOfIncludedUnits
            new_name = self.name + "_" + str(subset_number)
            new_soiu = SetOfIncludedUnits(name=new_name, unit_type_var=self.unit_type_var, specifying_variables=new_vars)
            soiu_subsets.append(new_soiu)
            subset_number+=1

        return soiu_subsets


                

class SetOfIncludedUnitsUnion(SetOfIncludedUnits):
    """
    This class describes the union of multiple SetOfIncludedUnits (abbreviation SOIU), 
    that cannot (yet) be neatly simplified to a regular SetOfIncludedUnits. All soiu's 
    in the list are a part of the union.
    
    """

    def __init__(self, set_of_soiu):
        # check that the unit type of the list of soiu's are all the same:
        unit_types = [soiu.unit_type_var for soiu in set_of_soiu]
        
        if len(set(unit_types)) > 1:
               # The list has more than one unit_type, so this union is not well defined
               # This situation should be avoided in SetOfIncludedUnits.union()
               raise BadUnionError("A union was attempted between sets of units with different unit types. " \
               "This led to a SetOfIncludedUnitsUnion that was not well defined.")
        
        self.unit_type_var = unit_types[0]  # all unit types are the same, so take the first one from the list

        self.set_of_soiu = set(set_of_soiu)  # list of individual SOIU's; automatically remove duplicates by using a set()

        self.name = " \u222a ".join(sorted(["("+soiu.name+")" if "\u2229" in soiu.name else soiu.name for soiu in set_of_soiu])) 
        # add brackets to soiu.name if it is an intersection (\u2229) of other soiu's, for readability

        

    def __str__(self):

        soiu_strs = sorted([str(soiu) for soiu in list(self.set_of_soiu)])
        
        # paste everything together
        selfstr = str(self.name) + ": {" + ", ".join(soiu_strs) + "}"
        
        return selfstr
    

    def is_subset(self, other: Union['SetOfIncludedUnits', 'SetOfIncludedUnitsUnion']):
        """
        Determines if SetOfIncludedUnitsUnion self is a subset of SOIU or SetOfIncludedUnitsUnion other.
        There are two ways self can be a subset of other. First, we check the fast option. 
        Second, we check the more complex option.
        """
        
        # For the two sets to be comparable, they must be defined on the same unit type
        if self.unit_type_var != other.unit_type_var:
            # Unit types don't match, operation not defined well, no subset
            return False

        # Gather the other soiu's (after this, the type of other does not matter anymore)
        if not isinstance(other, SetOfIncludedUnitsUnion):
            # A single soiu.
            other_soius = [other]
            # Prepare for option2. No need to determine minimum, because every variable occurs only once.
            minimum_granularities_other = {specvar.name: specvar.granularity for specvar in other.specifying_variables}
            
        else:
            # we know other is SetOfIncludedUnitsUnion
            other_soius = other.set_of_soiu
            # prepare for option2:
            minimum_granularities_other = other.get_minimum_granularities() 

        # Fastest option for self to be a subset of other:
        # For every soiu in self, there must be a soiu in other such that 
        # soiu_self is a subset of soiu_other (option1)
        # or soiu_self is a subset of the union of several soiu_other (option2)

        for soiu_self in self.set_of_soiu:
            # this must be true for every soiu_self
            # we are looking for any other soiu for which soiu_self is a subset of soiu_other
            
            if not any([soiu_self.is_subset(soiu_other) for soiu_other in other_soius]):
                # Option 1 did not find a soiu in other of which soiu_self is a subset.
                
                # adjust to smallest granularities common in soiuc other
                soiu_self_adjusted = soiu_self.adjust_granularities(minimum_granularities_other)  
                
                # Try option 2: perhaps soiu_self is a subset of a union of soiu's from other.
                for soiu_self_part in soiu_self_adjusted.split():
                    # loop over every set resulting from split(), which are sets that contain
                    # a single value for every specifying variable. The union of all soiu's resulting
                    # from split are again soiu self.
                    
                    # we are looking for any other soiu for which soiu_self is a subset of soiu_other
                    if not any([soiu_self_part.is_subset(soiu_other) for soiu_other in other_soius]):
                        # There is at least one of the split soiu's that is not contained in other, so it's not possible 
                        # that self is a subset of other
                        return False
                    
        # We made it out of the loop, so all soiu's are a subset of other 
        return True
        
        
    def intersection(self, other: Union['SetOfIncludedUnits', 'SetOfIncludedUnitsUnion']):
        # intersection of tho SOIU(C)

        if not isinstance(other, SetOfIncludedUnitsUnion):
            list_to_check = [other]
        else:
            # we know other is SetOfIncludedUnitsUnion
            list_to_check = other.set_of_soiu

        if self == other:
            # the intersection has no effect
            return self
        
        intersection_list = []
        for soiu_self in self.set_of_soiu:
            for soiu_other in list_to_check:
        
                # get the intersection of these two soiu's
                if intersection_tmp := soiu_self.intersection(soiu_other):
                    # intersection is possible 
                    intersection_list.append(intersection_tmp)

        new_list = list(set(intersection_list))
        return SetOfIncludedUnitsUnion(new_list)
        

    def union(self, other: Union['SetOfIncludedUnits', 'SetOfIncludedUnitsUnion']):
        # union of tho SOIU(C)
        
        if isinstance(other, SetOfIncludedUnits):
            list_to_add = [other]
        else:
            # we know other is SetOfIncludedUnitsUnion
            list_to_add = other.set_of_soiu

        if self == other:
            # the union has no effect
            return self

        new_set_of_soiu = self.set_of_soiu.union(list_to_add)

        return SetOfIncludedUnitsUnion(new_set_of_soiu)


    def get_minimum_granularities(self):
        """
        Returns a dictionary with minimum level of granularity for each specifying, across all soiu's.
        """
        # Initialise empty dictionary.
        min_gran = {}

        for soiu in self.set_of_soiu:
            for specvar in soiu.specifying_variables:
                if specvar.name not in min_gran:
                    # If the variable is not in the dictionary, add it with the current value
                    min_gran[specvar.name] = specvar.granularity
                elif specvar.granularity < min_gran[specvar.name]:
                    # Otherwise, update it only if the current value is smaller
                    min_gran[specvar.name] = specvar.granularity

        return min_gran

        