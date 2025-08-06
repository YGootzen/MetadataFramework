class Variable:
    # The smallest class in the framework. Each dataset contains multiple variables. Variables can have different levels of granularity. To change from one granularity to another, a conversion or aggregation is needed.
    
    def __init__(self, name = "dummy", granularity = 0):
        self.name = name
        self.granularity = granularity

    def __str__(self):
        return str(self.name) + str(self.granularity) 
    
    def __eq__(self, other: "Variable"):
        # compare self Variable object to the other Variable object
        # they are equal if the name and granularity are equal
        
        return all([self.name == other.name, 
                    self.granularity == other.granularity])
    
    def __hash__(self):
        # required for usage in sets. Since the str() of self is unique and contains all elements for equality, we use this for the hash.
        return(hash(str(self)))
    
    def equal_name(self, other: "Variable"):
        return self.name == other.name