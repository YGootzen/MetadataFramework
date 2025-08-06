from metadata_analysis.metadata.data import Data

def combines(data1: Data, data2: Data):
    # Create rowwise and colwise (in case combinations are not possible)
    rowwise, colwise = False, False
    
    # Combinations are only possible if the right-hand side variables are equal
    if data1.right_variables == data2.right_variables:
        # The result will have the same right-hand side variables 
        right3 = data1.right_variables
       
        # row-wise combination
        if set(data1.left_variables) & set(data2.left_variables):
            # there is overlap between the left variables 
            
            # row-wise merge possible     
            # no overlap between sets of included units of both sources, so only the same left-hand side variables can be merged
            left3 = set(data1.left_variables).intersection(set(data2.left_variables))  # intersection of L1 and L2
            units_3 = data1.set_of_units.union(data2.set_of_units)  # union of C1 and C3
            
            rowwise = Data(right_variables = right3, left_variables = left3, set_of_units = units_3,
                           name = "combine ("+data1.name+"+"+data2.name+")")
            
        # column-wise combination 
        if units_3:= data1.set_of_units.intersection(data2.set_of_units):
            # set1 & set2: checks if there exists an intersection between two sets
        
            # column-wise merge possible
            # set of included units of both input sources have overlap, so the left-hand variables can be merged
            left3 = set(data1.left_variables).union(set(data2.left_variables))  # union of L1 and L2
            # units_2 intersection of C1 and C2
            
            colwise = Data(right_variables = right3, left_variables = left3, set_of_units = units_3,
                           name = "combine ("+data1.name+"+"+data2.name+")")
        
    return rowwise, colwise