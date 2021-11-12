from bashparse.path_variable import path_variable
import bashlex


def shift_ast_pos(node, shift_amount):
    """The pos variable identifies where in the parsed string a particular value is. if the string gets longer we need to adjust it (ie var repalcement)
    shifts all the positions in an ast by a given value. Only useful if ast before this one gets x longer or shorter (happens on variable repalcement)
    super nice use but necessary if you want to do massive work with the framework. 
    returns the shifted tree (ie a bashlex.ast.node)"""
    
    node.pos = (node.pos[0] + shift_amount, node.pos[1] + shift_amount)
    if hasattr(node, 'parts'): 
        for part in node.parts:
            shift_ast_pos(part, shift_amount) 
    if hasattr(node, 'command'):  # some nodes are just pass through nodes
        shift_ast_pos(node.command, shift_amount)
    if hasattr(node, 'output'):   # some nodes are just pass through nodes
        shift_ast_pos(node.output, shift_amount)
    return node


def shift_ast_pos_to_start(node):
    return shift_ast_pos(node, node.pos[1])
    """shifts the pos variable so that it starts a 0. just a userful wrapper of the above class"""


# Make a version that only requires node and node_type
def execute_return_paths_to_node_type(node, current_path, paths, node_type):
    """(node, [], [], node type looking for) Finds all the paths to nodes in ast which are of a certain kind. 
	returns a list of path_variables to those nodes
	if you pass node type='parameter', it will find all the variables. the above find all variables is just convenient wrapper of this function"""
    
    if hasattr(node, 'parts') and len(node.parts): 
        for i in range(len(node.parts) - 1, -1, -1): paths = execute_return_paths_to_node_type(node.parts[i], current_path + [i], paths, node_type)
        # We iterate inreverse order here because the first elements we replace should be the farthest to the right in the string
        # This is so that the indexing doesn't change as we do the variable replacements. Will add section to maintain pos but for now
        # this is done this way to be safe and in the event that pos is added, it will work just the same 
    if hasattr(node, 'list') and len(node.list):
        for i in range(len(node.list) - 1, -1, -1): paths = execute_return_paths_to_node_type(node.list[i], current_path + [i], paths, node_type)
    # If its a redirect node, call the replacement on the node its redirection to
    if node.kind == 'redirect' and hasattr(node, 'output'): paths = execute_return_paths_to_node_type(node.output, current_path, paths, node_type) 
    # If its a command node, call the replacement on the node its actually referencing
    if hasattr(node, 'command'): paths = execute_return_paths_to_node_type(node.command, current_path, paths, node_type)
    # If the node is a parameter node, save its location into a variable path object
    if node.kind == node_type:
        paths += [ path_variable(path=current_path, node=node) ]   
    # We want an array of arrays so that we get a list of paths we can iterate through
    # Do not get greedy and try to do multiple paths per object. We need to preserve a very specific substitution order here
    return paths


def return_paths_to_node_type(node, node_type):
    return execute_return_paths_to_node_type(node, [], [], node_type)


def return_variable_paths(node):
    return execute_return_paths_to_node_type(node, [], [], 'parameter')


def convert_tree_to_string(node):
    command = None
    if hasattr(node, 'parts'):
        command = ""
        for el in node.parts:
            if el.kind == 'word': 
                command += el.word + ' '
            elif el.kind == 'redirect': 
                command +=  el.type + ' ' + el.output.word + ' '
        command = command[:-1]  # remove final space because thats wrong
    return command