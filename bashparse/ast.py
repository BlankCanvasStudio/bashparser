from bashparse.path_variable import path_variable
import bashlex


def shift_ast_pos(nodes, shift_amount):
    """The pos variable identifies where in the parsed string a particular value is. if the string gets longer we need to adjust it (ie var repalcement)
    shifts all the positions in an ast by a given value. Only useful if ast before this one gets x longer or shorter (happens on variable repalcement)
    super nice use but necessary if you want to do massive work with the framework. 
    returns the shifted tree (ie a bashlex.ast.node)"""
    if type(nodes) is not list: nodes = [nodes]
    for el in nodes:
        if type(el) is not bashlex.ast.node: raise ValueError('nodes must be a bashlex.ast.node')
    for node in nodes:
        node.pos = (node.pos[0] + shift_amount, node.pos[1] + shift_amount)
        # bashlex.ast.posshifter(shift_amount).visitnode(node)  # While this tenchnically works, its a lot more overhead
        if hasattr(node, 'parts'): 
            for part in node.parts:
                shift_ast_pos(part, shift_amount) 
        if hasattr(node, 'list'):
            for part in node.list:
                shift_ast_pos(part, shift_amount)
        if hasattr(node, 'command'):  # some nodes are just pass through nodes
            shift_ast_pos(node.command, shift_amount)
        if hasattr(node, 'output'):   # some nodes are just pass through nodes
            shift_ast_pos(node.output, shift_amount)
    return nodes


def shift_ast_pos_to_start(nodes):
    """shifts the pos variable so that it starts a 0. just a userful wrapper of the above class"""
    if type(nodes) is not list: nodes = [nodes]
    for el in nodes:
        if type(el) is not bashlex.ast.node: raise ValueError('nodes must be a bashlex.ast.node')
    shifted_nodes = []
    for node in nodes:
        shifted_nodes += shift_ast_pos(node, shift_amount=-nodes[0].pos[0])
    return shifted_nodes


def align_ast(node, start_index=None):
    if hasattr(node, 'output'): 
        start_index = align_ast(node.output, start_index)
        node.pos = (node.output.pos[0], node.output.pos[1])
    elif hasattr(node, 'command'):
        start_index = align_ast(node.command, start_index)
        node.pos = (node.command.pos[0], node.command.pos[1])

    elif hasattr(node, 'parts') and len(node.parts):
        for part in node.parts:
            start_index = align_ast(part, start_index)
        node.pos = (node.parts[0].pos[0], node.parts[-1].pos[1])
    elif hasattr(node, 'list') and len(node.list):
        start_index = align_ast(node.list[0], start_index)
        node.pos = (start_index, 0)
        for part in node.list[1:]:
            start_index = align_ast(part, start_index)
        node.pos = (node.pos[0], node.list[-1].pos[1])
    else:
        if hasattr(node, 'word'): node.pos = (node.pos[0], node.pos[0] + len(node.word))
        if hasattr(node, 'value'): node.pos = (node.pos[0], node.pos[0] + len(node.value)) 
        if start_index is None: start_index = node.pos[1]
    return start_index


# Make a version that only requires node and node_type
def execute_return_paths_to_node_type(node, current_path, paths, node_type):
    """(node, [], [], node type looking for) Finds all the paths to nodes in ast which are of a certain kind. 
	returns a list of path_variables to those nodes
	if you pass node type='parameter', it will find all the variables. the above find all variables is just convenient wrapper of this function"""
    
    if hasattr(node, 'parts') and len(node.parts): 
        for i in range(0, len(node.parts)): paths = execute_return_paths_to_node_type(node.parts[i], current_path + [i], paths, node_type)
        
    if hasattr(node, 'list') and len(node.list):
        for i in range(0, len(node.list)): paths = execute_return_paths_to_node_type(node.list[i], current_path + [i], paths, node_type)
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


def return_paths_to_node_type(nodes, node_type):
    if type(nodes) is not list: 
        if type(nodes) is bashlex.ast.node: return execute_return_paths_to_node_type(nodes, [], [], node_type)
        else: nodes = [nodes]
    for el in nodes:
        if type(el) is not bashlex.ast.node: raise ValueError('nodes msut be a bashlex.ast.node')
    paths = []
    for i in range(0, len(nodes)):
        paths += execute_return_paths_to_node_type(nodes[i], [i], [], node_type)
    return paths


def return_variable_paths(nodes):
    if type(nodes) is not list: nodes = [nodes]
    for el in nodes:
        if type(el) is not bashlex.ast.node: raise ValueError('nodes msut be a bashlex.ast.node')
    return return_paths_to_node_type(nodes, 'parameter')


def return_nodes_of_type(nodes, node_type):
    if type(nodes) is not list: nodes = [nodes]
    for el in nodes:
        if type(el) is not bashlex.ast.node: raise ValueError('nodes msut be a bashlex.ast.node')
    if type(node_type) is not str: raise ValueError('node_type must be a string')
    
    paths = return_paths_to_node_type(nodes, node_type)
    nodes = []
    for path in paths:
        nodes += [path.node]
    return nodes


def convert_tree_to_string(node):
    command = ""
    if hasattr(node, 'parts'):
        for part in node.parts: 
            if part.kind != 'parameter':
                command += convert_tree_to_string(part) + ' '
    elif hasattr(node, 'list'):
        for part in node.list:
            command += convert_tree_to_string(part) + ' '
    if node.kind == 'operator':
        command += node.op + ' '
    if hasattr(node, 'word'): 
        if ' ' in node.word: command += '"' + node.word + '"' + ' ' # Add quotes correctly
        else: command += node.word + ' ' # Parameters have values and should be ignore
    
    return command[:-1]  # Remove the extra space at end cause its wrong


def return_node_at_path(node, path):
    if type(node) is not bashlex.ast.node: raise ValueError('nodes must be made up of bashparse.node elements')
    if type(path) == path_variable: path = path.path 
    if type(path) is not list: raise ValueError('path must be a list')
    for el in path:
        if type(el) is not int: raise ValueError('elements of path list must be ints')
    
    if path == []: return node
    else:
        if hasattr(node, 'parts') and len(node.parts): return return_node_at_path(node.parts[path[0]], path[1:])
        
        elif hasattr(node, 'list') and len(node.list): return return_node_at_path(node.list[path[0]], path[1:])
        
        if node.kind == 'redirect' and hasattr(node, 'output'): return return_node_at_path(node.output, path)

        if hasattr(node, 'command'): return return_node_at_path(node.command, path)
