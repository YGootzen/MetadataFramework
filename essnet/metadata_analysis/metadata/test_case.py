
class TestCase:
    """
    For creating test cases with a starting set of sources, goal and models. 
    Note: the graphs should be created in the session and therefore loaded into memory.
    The path search algorihm will search directly in the memory, so there is no need
    to specify the graphs in a test case object.
    """
    def __init__(self, goal, start_set, models=None):
        self.goal = goal
        self.start_set = start_set
        self.models = models