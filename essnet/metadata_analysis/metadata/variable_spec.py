from metadata_analysis.metadata.variable import Variable
from metadata_analysis.metadata.aggregation import AggregationGraph

import copy as copy


class VariableSpec(Variable):
    # The `VariableSpec()` class is used in the definition of the set of included units in a datasource. It has similar 
    # properties to the original `Variable()` class and additionally contains information on the available values of that 
    # variable of the included units. Strata-completeness is a key term that distinguishes whether or not all possible 
    # values are available. It is different from the completeness in the sense that it does not guarantee all units of 
    # the target population are inlcuded, as some may not be due to errors in data collection. This last type of 
    # completeness may be included at a later date (potentially with a coverage rate, possibly per strata).

    def __init__(self, name, granularity, value_available = set()):
        super().__init__(name, granularity)  # create an instance of the original Variable() class

        # for descriptive usage in set of included units
        self.value_available = value_available  # set of available values in the set of included units

    def __str__(self):
        varvalues = sorted([str(vv) for vv in self.value_available])
        varvalues_str = ", ".join(varvalues)
        
        selfstr = str(self.name) + "_" + str(self.granularity) + ": {" + varvalues_str + "}"
        return selfstr
    
    def __eq__(self, other: "VariableSpec"):
        # compare self VariableSpec object to the other VariableSpec object
        # they are equal if the name, granularity and value_available are equal
        
        return all([self.name == other.name, 
                    self.granularity == other.granularity,
                    self.value_available == other.value_available])
    
    def __hash__(self):
        # Required for usage in sets. Since the str() of self is unique and contains all elements for equality, we use this for the hash.
        # Cannot be inherited from parent class Variable() because __eq__() was overridden.
        return(hash(str(self)))
    
    def is_complete(self):
        # Checks if the all possible values of self are present. Look up all possible values from an aggregation table.
        agg_graph = AggregationGraph.get(self.name)  # get aggregation graph
        all_possible_values = agg_graph.get_all_values(self.granularity)  # get all possible values
        
        # Compare the two sets (of available and all possible values). If they are equal, then the available values are complete.
        return self.value_available == all_possible_values

    
    def is_subset(self, other: 'VariableSpec'):
        # Returns true if the set of included units described by self (if it were the only specifying variable in the desription) 
        # is a subset of the set of included units described by other (if it were the only specifying variable in the desription)

        if self.name != other.name:
            # If the specifying variables are for different variable names, they are not subsets.
            return False

        if self.granularity == other.granularity:
            # In case of matching granularities: all we need to do is check that the values of self are a subset of the values of other.
            return self.value_available.issubset(other.value_available)
        
        # In case of non-matching granularities: we need to check if aggregation is possible between the values of these granularities, 
        # along a path with specified aggregation tables. We need a chained aggregation table. 
        
        agg_graph = AggregationGraph.get(self.name)  # get relevant aggregation graph

        if agg_table := agg_graph.get_aggregation_table(granularity_from = self.granularity, granularity_to = other.granularity):
            # we found an aggregation table, and know that self is of a smaller granularity than other
            # For self to be a subset of other. For every value in values(self), there must be a value in other,
            # such that T(key = value.other) is in values(other)
            # The value of other, is used as key in the aggregation table.
            potential_subset = True

            for value_self in self.value_available:
                # Search for a key in aggregation table such that: T(key) is in values(other)
                # any one key will do
                potential_subset = any([value_self in agg_table.value_map[value_other] for value_other in other.value_available])
                    
                if not potential_subset:
                    # there is no value_other to which value_self can be aggregated, so abort the search
                    # else, continue search
                    break
            return potential_subset

        elif agg_table := agg_graph.get_aggregation_table(granularity_from = other.granularity, granularity_to = self.granularity):
            # we found an aggregation table, and know that self is of a larger granularity than other
            # For self to be a subset of other: for every value in self, all values in the aggregation talbe values 
            # (with self value as key), must be present in the values of other

            potential_subset = True

            for value_self in self.value_available:
                # Loop over set of values (in the granularity of other) from aggregation table. All of these 
                # values must be present in other.values
                
                potential_subset = all([value_search in other.value_available for value_search in agg_table.value_map[value_self]])

                if not potential_subset:
                    # at least one value of translated values of self (into granualrity of the other, using 
                    # the aggregation table) is not available in other
                    break
            return potential_subset

        else:
            # In no direction can an aggregation table be constructed. This could either be because an aggregation is 
            # not possible, or because not enough aggregation tables were specified along the route.
            return False
        
        
    def intersection(self, other: 'VariableSpec'):
        # Returns the intersection of the set of included units described by self (if it were the only specifying variable in the desription) 
        # and the set of included units described by other (if it were the only specifying variable in the desription)

        if self.name != other.name:
            # If the specifying variables are for different variable names, an intersection is not defined
            return False
        
        if self.granularity == other.granularity:
            # In case of matching granularities: all we need to do is keep the intersection of the available values
            return VariableSpec(name = self.name,
                                granularity=self.granularity,
                                value_available=self.value_available.intersection(other.value_available))
        
        # In case of non-matching granularities: we need to check if aggregation is possible between the values of these granularities, 
        # along a path with specified aggregation tables. We may need a chained aggregation table. 
        
        agg_graph = AggregationGraph.get(self.name)  # get relevant aggregation graph

        if agg_table := agg_graph.get_aggregation_table(granularity_from = self.granularity, granularity_to = other.granularity):
            # we found an aggregation table, and know that self is of a smaller granularity than other
            
            spec_var_small = self
            spec_var_big = other

        elif agg_table := agg_graph.get_aggregation_table(granularity_from = other.granularity, granularity_to = self.granularity):
            # we found an aggregation table, and know that self is of a larger granularity than other
            
            spec_var_small = other
            spec_var_big = self

        else:
            # In no direction can an aggregation table be constructed. This could either be because an aggregation is 
            # not possible, or because not enough aggregation tables were specified along the route.
            # So, we cannot determine an intersection and will return False.
            return False
        
        # We now know which of the two sets is smaller (spec_var_small), which is bigger (spec_var_big) and the aggregation table
        # between the two (agg_table) from spec_var_small to spec_var_big
        result_value_available = set()
        # Loop over all values of the smaller set, and check if they should be part of the intersection
        for val_available_small in spec_var_small.value_available:
            if any([val_available_small in agg_table.value_map[value_available_big] for value_available_big in spec_var_big.value_available]):
                # There is at least one value available in the bigger granularity values, which the smaller value can be aggregated into
                result_value_available.add(val_available_small)

        # return the found result as a VariableSpec object
        return VariableSpec(name = self.name,
                            granularity = spec_var_small.granularity,
                            value_available = result_value_available)

    def union(self, other: 'VariableSpec'):
        # Returns the union of the set of included units described by self (if it were the only specifying variable in the desription) 
        # and the set of included units described by other (if it were the only specifying variable in the desription)

        if self.name != other.name:
            # If the specifying variables are for different variable names, a union is not defined
            return False
        
        if self.granularity == other.granularity:
            # In case of matching granularities: all we need to do is determine the union of the available values
            return VariableSpec(name = self.name,
                                granularity=self.granularity,
                                value_available=self.value_available.union(other.value_available))
        
        # In case of non-matching granularities: we need to check if aggregation is possible between the values of these granularities, 
        # along a path with specified aggregation tables. We may need a chained aggregation table. 
        
        agg_graph = AggregationGraph.get(self.name)  # get relevant aggregation graph

        if agg_table := agg_graph.get_aggregation_table(granularity_from = self.granularity, granularity_to = other.granularity):
            # we found an aggregation table, and know that self is of a smaller granularity than other
            
            spec_var_small = self
            spec_var_big = other

        elif agg_table := agg_graph.get_aggregation_table(granularity_from = other.granularity, granularity_to = self.granularity):
            # we found an aggregation table, and know that self is of a larger granularity than other
            
            spec_var_small = other
            spec_var_big = self

        else:
            # In no direction can an aggregation table be constructed. This could either be because an aggregation is 
            # not possible, or because not enough aggregation tables were specified along the route.
            # So, we cannot determine a union and will return False.
            return False
                
        # We now know which of the two sets is smaller (spec_var_small), which is bigger (spec_var_big) and the aggregation table
        # between the two (agg_table) from spec_var_small to spec_var_big
        result_value_available = copy.deepcopy(spec_var_small.value_available)

        # Loop over all values of the bigger set, and add their values (translated through the aggregation table) to the available set
        for val_available_big in spec_var_big.value_available:
            values_to_add = agg_table.value_map[val_available_big]
            for value_add in values_to_add:
                result_value_available.add(copy.deepcopy(value_add))

        # return the found result as a VariableSpec object
        return VariableSpec(name = self.name,
                            granularity = spec_var_small.granularity,
                            value_available = result_value_available)