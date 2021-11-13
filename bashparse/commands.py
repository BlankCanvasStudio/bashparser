import bashlex, copy
from bashparse.ast import return_paths_to_node_type, convert_tree_to_string

def find_specific_commands(nodes, commands_looking_for, saved_command_dictionary, return_as_strings):
    """(node, list of commands you're looking for, dict to save commands into, bool if the nodes should be saved as strings (and not ast nodes))
	This looks for given commands in an ast node. if it is a command then it gets saved to the dict
	Returns the updated command dictionary"""
    if type(nodes) is not list: nodes = [nodes]
    for node in nodes:
        if type(node) is not bashlex.ast.node: raise ValueError('node must be a bashlex.ast.node')
    if type(commands_looking_for) is not list: raise ValueError('commands_looking_for must be a list')
    for el in commands_looking_for:
        if type(el) is not str: raise ValueError('elements of commands_looking_for must be strings')
    if type(saved_command_dictionary) is not dict: raise ValueError('saved_command_dictionary must be a dictionary')
    if type(return_as_strings) is not bool: raise ValueError('return_as_string must be a bool')

    saved_command_dictionary = copy.deepcopy(saved_command_dictionary)  # preserve integrity of original dictionary

    for node in nodes:
        command_paths = return_paths_to_node_type(node, 'command')
        for path in command_paths:
            command_node = path.node
            if len(command_node.parts) and command_node.parts[0].word in commands_looking_for:
                if command_node.parts[0].word not in saved_command_dictionary: saved_command_dictionary[command_node.parts[0].word] = []
                if return_as_strings:
                    command = convert_tree_to_string(command_node)
                    if command not in saved_command_dictionary[command_node.parts[0].word]:
                        saved_command_dictionary[command_node.parts[0].word] += [copy.deepcopy(command)] # + saved_command_dictionary[command_node.parts[0].word]
                else:
                    if command_node not in saved_command_dictionary[command_node.parts[0].word]:
                            saved_command_dictionary[command_node.parts[0].word] += [copy.deepcopy(command_node)] # + saved_command_dictionary[command_node.parts[0].word]
    return saved_command_dictionary


def find_specific_command(nodes, command, return_as_strings):
    if type(nodes) is not list: nodes = [nodes]
    for node in nodes:
        if type(node) is not bashlex.ast.node: raise ValueError('node must be a bashlex.ast.node')
    command_dict = {command:[]}
    for node in nodes:
        command_dict = find_specific_commands(node, [command], command_dict, return_as_strings)
    return command_dict[command]


def return_commands_from_variable_delcaraction(nodes):
    """(node) strips the commands from a variable declaration if its of the form a=$(some command)\
	returns a list of any commands found in the node"""
    if type(nodes) is not list: nodes = [nodes]
    for node in nodes:
        if type(node) is not bashlex.ast.node: raise ValueError('node must be a bashlex.ast.node')
    
    commands = []
    for node in nodes:
        assignments = return_paths_to_node_type(node, 'assignment')
        for assignment in assignments:
            command_substitutions = return_paths_to_node_type(assignment.node, 'commandsubstitution')
            for substitution in command_substitutions:
                commands += return_commands_from_command_substitutions(substitution.node)
    return commands


def return_commands_from_command_substitutions(nodes):
    if type(nodes) is not list: nodes = [nodes]
    for node in nodes:
        if type(node) is not bashlex.ast.node: raise ValueError('node must be a bashlex.ast.node')
    commands = []
    for node in nodes:
        command_substitutions = return_paths_to_node_type(node, 'commandsubstitution')
        for substitution in command_substitutions:
            commands = [copy.deepcopy(substitution.node.command)] + commands  # pass by reference so need to copy to stay seperate
    return commands


def return_commands_from_for_loops(nodes):
    if type(nodes) is not list: nodes = [nodes]
    for node in nodes:
        if type(node) is not bashlex.ast.node: raise ValueError('node must be a bashlex.ast.node')
    commands = []
    for node in nodes:
        for_loops = return_paths_to_node_type(node, 'for')
        for loop in for_loops:
            command_nodes = return_paths_to_node_type(loop.node, 'command')
            for command in command_nodes:
                commands += [copy.deepcopy(command.node)]
    return commands