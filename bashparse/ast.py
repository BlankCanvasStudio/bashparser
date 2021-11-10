from bashparse.path_variable import path_variable
import bashlex


def shift_ast_pos(node:bashlex.ast.node, shift_amount):
    node.pos = (node.pos[0] + shift_amount, node.pos[1] + shift_amount)
    if hasattr(node, 'parts'): 
        for part in node.parts:
            shift_ast_pos(part, shift_amount) 
    if hasattr(node, 'command'):  # some nodes are just pass through nodes
        shift_ast_pos(node.command, shift_amount)
    if hasattr(node, 'output'):   # some nodes are just pass through nodes
        shift_ast_pos(node.output, shift_amount)
    return node


def shift_ast_pos_to_start(node:bashlex.ast.node):
    return shift_ast_pos(node, node.pos[1])  # EZPZ


def return_paths_to_node_type(node: bashlex.ast.node, current_path: list, paths: list, node_type:str):
    if hasattr(node, 'parts') and len(node.parts): 
        for i in range(len(node.parts) - 1, -1, -1): paths = return_paths_to_node_type(node.parts[i], current_path + [i], paths, node_type)
        # We iterate inreverse order here because the first elements we replace should be the farthest to the right in the string
        # This is so that the indexing doesn't change as we do the variable replacements. Will add section to maintain pos but for now
        # this is done this way to be safe and in the event that pos is added, it will work just the same 
    # If its a redirect node, call the replacement on the node its redirection to
    if node.kind == 'redirect' and hasattr(node, 'output'): paths = return_paths_to_node_type(node.output, current_path, paths, node_type) 
    # If its a command node, call the replacement on the node its actually referencing
    if hasattr(node, 'command'): paths = return_paths_to_node_type(node.command, current_path, paths, node_type)
    # If the node is a parameter node, save its location into a variable path object
    if node.kind == node_type:
        paths += [ path_variable(path=current_path, node=node) ]   
    # We want an array of arrays so that we get a list of paths we can iterate through
    # Do not get greedy and try to do multiple paths per object. We need to preserve a very specific substitution order here
    return paths


def return_variable_paths(node: bashlex.ast.node, current_path: list, paths: list):
    return return_paths_to_node_type(node, current_path, paths, 'parameter')
