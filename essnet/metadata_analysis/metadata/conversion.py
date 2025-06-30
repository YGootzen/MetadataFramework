import networkx as nx
import copy as copy
import warnings

from metadata_analysis.metadata.errors import NotInitialisedError

class ConversionGraph:
    instances = []  # class attribute to keep track of class instances
    
    def __init__(self, variable_name, granularities, conversion_edges):
        self.variable_name = variable_name
        self.Graph = nx.Graph()
        self.granularities = granularities

        for g in granularities:
            self.Graph.add_node(g)

        for e in conversion_edges:
            self.Graph.add_edge(*e)  # * unpacks edge tuple
        
        # add self to list of instances
        if self.is_initialised(variable_name):
            # an instance with this variable name was already known, remove that instance (so the new instance is the only one)
            ConversionGraph.instances.remove(self.get(variable_name))
            warnings.warn("Overwriting the ConversionGraph for variable "+str(variable_name)+"!")
            
        ConversionGraph.instances.append(self)  # append instance to list of class instances
        
    @classmethod 
    def get(cls: "ConversionGraph", var_name):
        # return the instance of this class for which the value variable_name is equal to var_name
        # each ConversionGraph object should exist exactly once for each variable_name
        
        # first we make a list of "all" instances that statisfy the desired variable name
        list_form = [inst for inst in cls.instances if inst.variable_name == var_name]
        if len(list_form) > 0:
            # list is not empty, so return the first element (there should only be one)
            return list_form[0]
           
        else:
            # no instance was found
            raise NotInitialisedError("ConversionGraph " + var_name)
            
    def get_max_granularities(self):
        return max(self.granularities)
        
    def is_initialised(cls: "ConversionGraph", var_name):
        list_form = [inst for inst in cls.instances if inst.variable_name == var_name]
        return len(list_form) > 0

    def add_granularity(self, new_granularity):
        self.Graph.add_node(new_granularity)

    def add_conversion_edge(self, new_edge):
        self.Graph.add_edge(*new_edge)

    def plot_graph(self):
        nx.draw(self.Graph, with_labels=True, node_color="lightgrey")
        
    def check_conversion(self, granularity_from, granularity_to):
        # true: if there is a conversion path between granularity_from to granularity_to
        # false: otherwise
        return nx.has_path(self.Graph, granularity_from, granularity_to)
    
    def all_conversions(self, granularity_from):
        # returns all possible granularities that can be reached from the granularity_from
        connected_set = nx.node_connected_component(self.Graph, granularity_from)  # this includes the starting node
        connected_set.remove(granularity_from)  # exclude starting node
        return connected_set