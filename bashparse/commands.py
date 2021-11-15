import bashlex, copy
from bashparse.ast import return_paths_to_node_type, convert_tree_to_string, return_node_at_path

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


def return_command_aliasing(nodes, command_alias_list = {}):
    if type(nodes) is not list: nodes = [nodes]
    for node in nodes: 
        if type(node) is not bashlex.ast.node: raise ValueError('nodes must be a bashlex.ast.node')
    if type(command_alias_list) is not dict: raise ValueError('command_alias_list must be a dictionary')
    for node in nodes:
        command_nodes = return_paths_to_node_type(node, 'command')
        for command in command_nodes:
            if len(command.node.parts) > 2 and ( command.node.parts[0].word == 'mv' or command.node.parts[0].word == 'cp' ):
                non_flag_base = 1
                while non_flag_base + 1 < len(command.node.parts) and command.node.parts[non_flag_base].word[0] == '-':
                    non_flag_base += 1
                if command.node.parts[non_flag_base].word in command_alias_list:
                    command.node.parts[non_flag_base].word = command_alias_list[command.node.parts[non_flag_base].word]
                command_alias_list[command.node.parts[non_flag_base + 1].word] = command.node.parts[non_flag_base].word
                if '/' in command.node.parts[non_flag_base].word: command.node.parts[non_flag_base].word = command.node.parts[non_flag_base].word.split('/')[-1]
                if '/' in command.node.parts[non_flag_base + 1].word: command.node.parts[non_flag_base + 1].word = command.node.parts[non_flag_base + 1].word.split('/')[-1]
                command_alias_list[command.node.parts[non_flag_base + 1].word] = command.node.parts[non_flag_base].word
    
    return command_alias_list


def replace_command_aliasing(nodes, command_alias_list = {}):
    if type(nodes) is not list: nodes = [nodes]
    for node in nodes: 
        if type(node) is not bashlex.ast.node: raise ValueError('nodes must be a bashlex.ast.node')
    if type(command_alias_list) is not dict: raise ValueError('command_alias_list must be a dictionary')
    
    to_return = []
    for node in nodes:
        top_level_node = copy.deepcopy(node)
        command_nodes = return_paths_to_node_type(top_level_node, 'command')
        for command in command_nodes:
            current_node = return_node_at_path(top_level_node, command.path)
            if len(current_node.parts) and command.node.parts[0].word in command_alias_list:
                current_node.parts[0].word = command_alias_list[current_node.parts[0].word] 
        to_return += [ top_level_node ]
    
    return to_return


def resolve_command_aliasing(nodes, command_alias_list={}):
    if type(nodes) is not list: nodes = [nodes]
    for node in nodes: 
        if type(node) is not bashlex.ast.node: raise ValueError('nodes must be a bashlex.ast.node')
    if type(command_alias_list) is not dict: raise ValueError('command_alias_list must be a dictionary')

    command_alias_list = {}
    unaliased_commands = []
    for node in nodes:
        command_alias_list = return_command_aliasing(node, command_alias_list)
        unaliased_commands += replace_command_aliasing(node, command_alias_list)
    
    return unaliased_commands


