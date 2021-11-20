import copy 

class path_variable:
    def __init__(self, path, node):
        self.path = path
        self.node = copy.deepcopy(node)  # This could be a mistake but we are rolling with it
        self.value = None  # This is a flex spot to hold a vaslue associated with this path_var
            # Its used in this code to hold the value of a variable located at the end of the path
    def __repr__(self):
        path = '[' + ','.join(str(x) for x in self.path) + ']'
        return "path_var(" + path + ', ' + str(self.node) + ')'
    def __str__(self):
        path = '[' + ','.join(str(x) for x in self.path) + ']'
        return "path_var(" + path + ', ' + str(self.node) + ')'
    def __eq__(self, obj):
        return obj.path == self.path
