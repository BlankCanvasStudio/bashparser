# bashparse: A python library for bash file interpretation

bashparse is a python library containing a number of helpful tools to contextualize bash scripts.

## Dependencies

    This package only depends on bashlex

## Function Descriptions

- parse(str): A wrapper for bashlex.parse. Takes a string as an argument and returns an abstract syntax tree (a bashlex.ast.node object)

- path_varaible: an object which holds a path, a node, which can be found at the end of that path, and an optional value field (used in this package when the node is a variable and has a corresponding value). 
    
- update_variable_list(node: bashlex.ast.node, var_list: dict): Takes a node object and variable list. Returns a dictionary. This function finds any variable declarations in the abstract syntax tree and saves the name value pair to the dictionary passed in, such that you can index by variable name and return the variable's value. Note, the variables value will always be returned as an array.
- substitute_variables(node: bashlex.ast.node, var_list: dict): Takes an ast node and a variable dict. Returns an array of nodes. This function identifies all the variables that need replacement in the node passed in. It then referencesd the var_list to identify if a definition for that variable exists. If a definition exists, it will suibstitute the value. In the event the variable has multiple values (i.e. is an array), multiple nodes corresponding to all the possible replacements will be returned.
- add_variables_to_var_list(var_list: dict, name: str, value: str/array): Takes the variable list, the name of the variable, and the value(s) to assign to the . This function adds an index into the variable dict with the value(s) passed into the function. This will add the specified values into the dict index if the value already exists. This just makes sure that all values in the dictionary are arrays. THIS IS NECESSARY FOR THE VARIABLES SECTION OF THE PACKAGE TO WORK
- replace_variables(node: bashlex.ast.node, paths: list of path_variables, var_list: dict): Returns a list of nodes. Takes a node, paths to all the variables you want to replace, and a variable list with the corresponding values. This function replaces all the variables in the paths list with their corresponding values in the var_list dictionary. The function then returns an array of all the possible combinations of variable replacements, according to bash's rules. If a varible does not exist in the var_list, then it will not be changed. The ast will have its pos variables changed accordingly and the parameter nodes will be removed if the replacement occurs. 
    
- node_level_regex(node: bashlex.ast.node, regex:r"str"): Takes the node and the regex you'd like to find in the ast. Returns a list of strings which match the regex. This traverse every node in the ast and checks if part of the word matches the regex. If it does, the matching regex is added to a list, which is returned.        

- find_specific_commands(node: bashlex.ast.node, commands_looking_for: list of str, saved_command_dictionary: dict, return_as_string: bool): This function checks the ast for exections of commands listed in the commands_looking_for. If the command is found in the ast than an array of either command nodes or the command strings.
- return_commands_from_variable_delcaraction(node: bashlex.ast.node): This function returns any commands that would be executed in a variable declaration via a command substitution. I.e. a=$(wget www.google.com). Returns an array of nodes corresponding to the commands executed.

- shift_tree_pos(node:bashlex.ast.node, shift_amount:int): This takes a node and the amount to shift all the pos values by. This is used to shift a nodes to start at any given value, instead of its offset in the string. Returns the node with the updated pos values 
- shift_tree_pos_to_start(node: bashlex.ast.node): Shifts a given node pos to starting at 0. A helpful wrapper of the above function. Returns the newly shifted node
- return_paths_to_node_type(node:bashlex.ast.node, current_path: list of ints, paths: list of path_variables, node_type: str): This function iterates through the given ast to find the location of all the nodes which are of kind node_type. It then returns a list of path_variables which can be used to identify and traverse to the given nodes. current_path and paths should be empty on initial call 
- return_variable_paths(node: bashlex.ast.node, current_path:list of ints, paths:list of path_variables): This function is a helpful wrapper to the above function. Should be used to find all the varaibles used in the node. Returns a list of the path_variables which can be used to identify all the variables in the node.

