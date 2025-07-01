import copy as copy
import warnings
import networkx as nx

from metadata_analysis.metadata.errors import NotInitialisedError
#from aggregation_table import AggregationTable

class AggregationGraph:
    instances = []  # class attribute to keep track of class instances
    
    def __init__(self, variable_name, granularities, aggregation_edges):
        self.variable_name = variable_name
        self.Graph = nx.DiGraph()
        self.granularities = granularities

        for g in granularities:
            self.Graph.add_node(g)

        for e in aggregation_edges:
            self.Graph.add_edge(*e)  # * unpacks edge tuple
            
        # add self to list of instances
        if self.is_initialised(variable_name):
            # an instance with this variable name was already known, remove that instance (so the new instance is the only one)
            AggregationGraph.instances.remove(self.get(variable_name))
            warnings.warn("Overwriting the AggregationGraph for variable "+str(variable_name)+"!")
        AggregationGraph.instances.append(self)  # append instance to list of class instances
            
    @classmethod 
    def get(cls: "AggregationGraph", var_name):
        # return the instance of this class for which the value variable_name is equal to var_name
        # each AggregationGraph object should exist exactly once for each variable_name

        # first we make a list of "all" instances that statisfy the desired variable name
        list_form = [inst for inst in cls.instances if inst.variable_name == var_name]
        if len(list_form) > 0:
            # list is not empty, so return the first element (there should only be one)
            return list_form[0]
        else:
            # no instance was found
            raise NotInitialisedError("AggregationGraph " + var_name)
            
    def is_initialised(cls: "AggregationGraph", var_name):
        list_form = [inst for inst in cls.instances if inst.variable_name == var_name]
        return len(list_form) > 0

    def get_max_granularities(self):
        return max(self.granularities)        

    def add_granularity(self, new_granularity):
        self.Graph.add_node(new_granularity)

    def add_aggregation_edge(self, new_edge):
        self.Graph.add_edge(*new_edge)  # * unpacks edge tuple

    def plot_graph(self): 
        # Legenda: 
        # Black: no aggregation table specified
        # Blue: aggregation table specified
        # Solid line: original edge
        # Dotted line: shortcut edge (created by chaining two AggregationTables)

        colors = []
        styles = []

        # determine colors and line style for each edge:
        for u,v in self.Graph.edges:
            
            if "AggregationTable" in self.Graph.edges[u,v]:
                colors.append("blue")

                if len(self.Graph.edges[u,v]["AggregationTable"].shortcut_path)>0:
                    # The AggregationTable is the result of a chaining of other AggregationTables
                    styles.append("dotted")
                else:
                    styles.append("solid")
            else:
                colors.append("black")
                styles.append("solid")

        base_size = 350  # base size of node
        nx.draw(self.Graph, 
                with_labels=True, 
                node_color="lightgrey", 
                node_size=[len(str(node_tmp)) *base_size for node_tmp in self.Graph.nodes()],  # scale nodes with number of characters in string
                edge_color=colors, 
                style=styles)

    def check_aggregation(self, granularity_from, granularity_to):
        # Checks whether a path exists in the aggregation graph from granularity_from to granularity_to.
        # true: if there is an aggregation path between granularity_from to granularity_to
        # false: otherwise

        return nx.has_path(self.Graph, granularity_from, granularity_to)
    
    def all_aggregations(self, granularity_from):
        # returns all possible granularities that can be reached from the granularity_from
        reacheable_set = nx.descendants(self.Graph, granularity_from) 
        
        return reacheable_set
        
    def all_aggregations_reversed(self, granularity_to):
        # returns all possible granularities from which the granularity_from can be reached 
        reacheable_set = nx.ancestors(self.Graph, granularity_to) 
        
        return reacheable_set
    
    def set_aggregation_table(self, granularity_from, granularity_to, agg_table: "AggregationTable"):
        # This may be an aggregation table for an existing edge.
        try:
            # Edge exists in the graph, so we can simply add the AggregationTable
            self.Graph.edges[granularity_from, granularity_to]["AggregationTable"] = agg_table

        except KeyError:
            # If the edge did not exist yet, a KeyError will occur. 
            # We need to create the new edge. This edge is possibly created as a 
            # shortcut by chaining two AggregationTables of existing (neighbouring) edges
            self.Graph.add_edge(granularity_from, granularity_to)
            # Now that the edge exists, we can add the AggregationTable
            self.Graph.edges[granularity_from, granularity_to]["AggregationTable"] = agg_table

    def get_aggregation_table(self, granularity_from, granularity_to):
        # Returns aggregation table if it is available in this aggregation graph. Returns a compounded aggregation
        # table if possible (only if no direct route is possible).

        if granularity_from == granularity_to:
            # No need to aggregate between the same granularity
            return False

        try: 
            # See if there is a single edge in the graph with a specified AggregationTable
            agg_table = self.Graph.edges[granularity_from, granularity_to]["AggregationTable"]
            
        except KeyError:
            # If the aggregation table was never defined, a KeyError will occur. We now know there
            # is no single edge with the requested aggregation table. It is possible however, that an aggregation
            # table can be constructed from granularity_from to granularity_to if a path exists for which
            # every edge has a specified aggregation table. Chaining the tables from the edges along
            # the path into a new mapping, gives us the desired aggregation table. 

            # Create a copy of the graph, where only edges are used that have a specified aggregation table
            agg_graph_specified = copy.deepcopy(self.Graph)
            for u,v in self.Graph.edges:
                # Loop over all edges, and remove them if they do not have a specified aggregation table
                if not "AggregationTable" in self.Graph.edges[u,v]:
                    # This edge does not have an aggregation table, so remove it
                    agg_graph_specified.remove_edge(u,v)

            # Find the shortest path for which aggregation tables are specified. We chose the shortest path, 
            # to minimise the number of steps where assumptions influence the final compound aggregation table
            try: 
                compound_path = nx.shortest_path(agg_graph_specified, granularity_from, granularity_to)
            except nx.NetworkXNoPath:
                # There is no path possible out of edges with specified aggregation tables
                return False
            
            # compound_path is of the form [granularity_from, node1, node2, ... ,granularity_to]
            # we know there is at least one node1 because otherwise an aggregation table for this edge would alreadybe specifieds
            
            print("compound_path", compound_path)
            # Start with the first aggregation table along the path
            agg_table_compound = self.Graph.edges[compound_path[0], compound_path[1]]["AggregationTable"]

            # Loop over all edges on the path to chain their aggregation tables:
            for node_index in range(1, len(compound_path)):
                agg_table_to_add = self.Graph.edges[compound_path[node_index], compound_path[node_index+1]]["AggregationTable"]
                agg_table_compound = agg_table_compound.chain(agg_table_to_add)

            # Within chain(), the newly created aggregation table is added to the graph, 
            # to save time if it is needed again later. 
            # These added edges will be given a "shortcut_path" so we can always look back 
            # on which original aggregation tables were used to construct the shortcut table. This may be helpful
            # to print to a log file, in case multiple paths result in variants of the shortcut table due to 
            # (real-life) assumptions in the aggregation tables along the path. 
            
            agg_table = agg_table_compound
            
        return agg_table
    
    def get_connected_aggregation_tables(self, granularity):
        # return a list of all aggregation tables where granularity is granularity_from or granularity_to

        # granularity is granularity_from: 
        potential_gran_to = self.all_aggregations(granularity_from=granularity)
        from_tables = [self.get_aggregation_table(granularity_from=granularity, granularity_to=gt) for gt in potential_gran_to]  # may contain False values if not all aggregation tables are specified
        from_tables_nofalse = [x for x in from_tables if x]  # remove False values

        # granularity is granularity_to: 
        potential_gran_from = self.all_aggregations_reversed(granularity_to=granularity)
        to_tables = [self.get_aggregation_table(granularity_from=gt, granularity_to=granularity) for gt in potential_gran_from]  # may contain False values if not all aggregation tables are specified
        to_tables_nofalse = [x for x in to_tables if x]  # remove False values

        return from_tables_nofalse, to_tables_nofalse
    
    def get_all_values(self, granularity):
        # return all possible values for this granularity of the variable, based on the aggregation tables

        # an AggregationTable's value_map is a dictionary of the form:
        # {0: {a,b}, 1:{c,d}, 2:{e,f,g}}
        # the dictionary's keys are values that belong to the "granularity_to" (A1)
        # the dictionary's values are (sets of) values that belong to the "granularity_from" (A0)

        # get all aggregation tables
        from_tables, to_tables = self.get_connected_aggregation_tables(granularity)

        if from_tables:
            # these tables have the granularity of interest as granularity_from, with another granularity_to (that is not of interest)
            # the values of interest are in the .values() of the dictionary
            # a value in the value_map can be a set of multiple elements
            from_values = [value for ft in from_tables for set_of_values in ft.value_map.values() for value in set_of_values]

        if to_tables:
            # these tables have the granularity of interest as granularity_from, with another granularity_to (that is not of interest)
            # the values of interest are in the .values() of the dictionary
            # a key is always one element
            to_values = [value for ft in to_tables for value in ft.value_map.keys()]  

        # If all AggregationTables are complete, we would only need to look at one table to find the complete list of possible values
        # Since this may not always be the case, we look at all, and take the union of all values found
        all_possible_values = set(from_values).union(set(to_values))

        return all_possible_values
        
        
class AggregationTable:
    instances = []  # class attribute to keep track of class instances
    
    def __init__(self, variable_name, granularity_from, granularity_to, value_map, shortcut_path=[]):
        # Aggregation table describes the relation between values along one edge of an aggregation graph. 
        # Currently implemented for discrete variables only. 
        self.variable_name = variable_name
        self.granularity_from = granularity_from
        self.granularity_to = granularity_to
        self.value_map = value_map  

        # path may be specified when a shortcut edge is created, chaining different aggregation tables along a path (this is 
        # an empty list for original aggregation tables available from the input)
        self.shortcut_path = shortcut_path 
        
        # Example of value_map:
        # Variable A0 with values {a,b,c,d,e,f,g} and A1 with values {0,1,2}
        # value_map is a dictionary of the form:
        # {0: {a,b}, 1:{c,d}, 2:{e,f,g}}
        # the dictionary's keys are values that belong to the "granularity_to" (A1)
        # the dictionary's values are (sets of) values that belong to the "granularity_from" (A0)

        # add self to list of instances
        if self.is_initialised(variable_name, granularity_from, granularity_to):
            # an instance with this variable name was already known, remove that instance (so the new instance is the only one)
            AggregationTable.instances.remove(self.get(variable_name, granularity_from, granularity_to))
            warnings.warn("Overwriting the AggregationTable for variable "+str(variable_name)+": from "+ 
                          str(granularity_from)+ " -> " + str(granularity_to) + "!")
        AggregationTable.instances.append(self)  # append instance to list of class instances

        # add self to the aggregation graph of the variable
        agg_self = AggregationGraph.get(variable_name)
        agg_self.set_aggregation_table(granularity_from, granularity_to, self)

    def __str__(self):
        # Create string to display the aggregation table
        selfstr = "AggregationTable of variable " + str(self.variable_name) + ": "+ str(self.granularity_from) + " -> "

        if self.shortcut_path:
            # if this aggregation table was created by chaining other aggregation tables in the aggregation graph, we want 
            # to show the path used to create the aggregation table. This may help the user in case multiple paths are
            # available that may have different underlying assumptions.
            selfstr += " -> ".join([str(x) for x in self.shortcut_path]) + " -> "

        selfstr += str(self.granularity_to)+ "."

        to_join = []
        # Ensure the value map is printed in a nice sorted order (for both keys and values)
        for key in sorted(list(self.value_map.keys())):
            to_append = "      "+str(key) + ": {"
            to_append += ", ".join(sorted([str(x) for x in self.value_map[key]]))
            to_append += "}"

            to_join.append(to_append)

        valmapstr = ",\n".join(to_join)

        selfstr += " Map: \n" + valmapstr 

        return selfstr
        
    @classmethod 
    def get(cls: "AggregationTable", var_name, granularity_from, granularity_to):
        # return the instance of this class for which the value variable_name is equal to var_name
        # each AggregationGraph object should exist exactly once for each variable_name

        # first we make a list of "all" instances that statisfy the desired variable name, granularity_from and granularity_to
        list_form = [inst for inst in cls.instances if (inst.variable_name == var_name and 
                                                        inst.granularity_from == granularity_from and 
                                                        inst.granularity_to == granularity_to)]
        if len(list_form) > 0:
            # list is not empty, so return the first element (there should only be one)
            return list_form[0]
        else:
            # no instance was found
            raise NotInitialisedError("AggregationTable " + var_name + " " + str(granularity_from) + " to " + str(granularity_to))

    def is_initialised(cls: "AggregationTable", var_name, granularity_from, granularity_to):
        list_form = [inst for inst in cls.instances if (inst.variable_name == var_name and 
                                                        inst.granularity_from == granularity_from and 
                                                        inst.granularity_to == granularity_to)]
        return len(list_form) > 0
    
    def get_translated_variables(self, values_to):
        """
        Return all values that can be reached from the set of available values in granularity_from, in granularity_to.
        values_to: set of values in the "to" granularity
        """
        values_from = set()  # empty set
        
        for val_to in values_to:
            # add reachable values_from from the values_to
            values_from.update(self.value_map[val_to])
        
        return values_from


    def chain(self, other: "AggregationTable"):
        # Merge two aggregation tables into one new aggregation table. Not sensitive to the order in which the 
        # two tables are presented.

        if self.variable_name != other.variable_name:
            warnings.warn("Trying to chain two aggregation tables that are not defined for the same variable!")
            return False

        # Determine order of the two aggregation graphs. This determined the starting granularity (gran_from),
        # ending granularity (gran_to), what value maps should be followed in what order and what the resulting
        # shortcut_path looks like. 
        if self.granularity_to == other.granularity_from:
            # e.g. self: 0->1 and other: 1->2 
            gran_from = self.granularity_from
            gran_mid = self.granularity_to  # same as other.granularity_from
            gran_to = other.granularity_to

            map_from_mid = self.value_map 
            map_mid_to = other.value_map

            # Append shortcut_path with new addition of mid point
            shortcut_path_chained = self.shortcut_path + [gran_mid] + other.shortcut_path

        elif self.granularity_from == other.granularity_to:
            # e.g. self: 1->2 and other: 0->1 
            gran_from = other.granularity_from
            gran_mid = other.granularity_to  # same as self.granularity_from
            gran_to = self.granularity_to

            map_from_mid = other.value_map 
            map_mid_to = self.value_map

            # Append shortcut_path with new addition of mid point
            shortcut_path_chained = other.shortcut_path + [gran_mid] + self.shortcut_path

        else:
            warnings.warn("Trying to chain two aggregation tables without a common granularity!")
            return False
        
        # Now we can be certain of how to interpret the two input tables. 
        # We have two maps: map_from_mid: gran_from -> gran_mid and map_mid_to: gran_mid -> gran_to

        # Initiate map_chained as new value_map for chained table. 
        map_chained = dict()

        # The keys of our new map_chained are the keys from map_mid_to
        for key_chain in map_mid_to.keys(): 
            map_chained[key_chain] = set()  # start with empty set of values

        # The values of our new map_chained are values from map_from_mid, determined via the gran_mid
        for key_mid, val_from in map_from_mid.items():
            # Assign val_from to the correct key in map_chained. 
            
            for key_to, val_mid in map_mid_to.items():
                # check if this is the correct combination
                # val_mid is a set of values, key_mid is a single value
                
                if key_mid in val_mid:
                    # This is the correct combination! Add the val_from to the new map_chain at position key_to
                    for val_from_element in list(val_from):
                        # Add each element of the values (which may be a set with multiple values) at position key_to
                        map_chained[key_to].add(val_from_element)

                    # No need to continue in the inner for loop since a match was found
                    break 

        at_chained = AggregationTable(variable_name=self.variable_name, granularity_from=gran_from, granularity_to=gran_to, 
                            value_map=map_chained,
                            shortcut_path = shortcut_path_chained)

        return at_chained

