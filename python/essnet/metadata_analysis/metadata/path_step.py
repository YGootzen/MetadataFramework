
class Step:
    def __init__(self, method="", method_detail="", input="", output=""):
        self.method = method
        self.method_detail = method_detail

        if isinstance(input, list):
            # a single data set is the input, it was not put into a list, so do that now
            self.input = input
        else:
            self.input = [input]

        if isinstance(output, list):
            # a single data set is the output, it was not put into a list, so do that now
            self.output = output
        else:
            self.output = [output]

    def __hash__():
        str_to_hash = str(self.method) + str(self.method_detail) + [str(
            data_in) for data_in in self.input] + [str(data_out) for data_out in self.output]
        
        return hash(str_to_hash)