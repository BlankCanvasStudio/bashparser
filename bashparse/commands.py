import bashlex, copy
from bashparse.ast import return_paths_to_node_type

def find_specific_commands(node, commands_looking_for, saved_command_dictionary, return_as_string):
    """(node, list of commands you're looking for, dict to save commands into, bool if the nodes should be saved as strings (and not ast nodes))
	This looks for given commands in an ast node. if it is a command then it gets saved to the dict
	Returns the updated command dictionary"""
    if type(node) is not bashlex.ast.node: raise ValueError('node must be a bashlex.ast.node')
    if type(commands_looking_for) is not list: raise ValueError('commands_looking_for must be a list')
    for el in commands_looking_for:
        if type(el) is not str: raise ValueError('elements of commands_looking_for must be strings')
    if type(saved_command_dictionary) is not dict: raise ValueError('saved_command_dictionary must be a dictionary')
    if type(return_as_string) is not bool: raise ValueError('return_as_string must be a bool')

    if node.kind == 'for' or node.kind == 'list':
        for part in node.parts:
            saved_command_dictionary = find_specific_commands(part, commands_looking_for, saved_command_dictionary, return_as_string)
    if node.kind == 'commandsubstitution':
        if hasattr(node, 'parts'):
            for part in node.parts:
                saved_command_dictionary = find_specific_commands(part, commands_looking_for, saved_command_dictionary, return_as_string)
        saved_command_dictionary = find_specific_commands(node.command, commands_looking_for, saved_command_dictionary, return_as_string)
    if node.kind == 'compound':
        for part in node.list:
            saved_command_dictionary = find_specific_commands(part, commands_looking_for, saved_command_dictionary, return_as_string)
    elif node.kind == 'command' and node.parts[0].word in commands_looking_for:
            if node.parts[0].word not in saved_command_dictionary: saved_command_dictionary[node.parts[0].word] = []
            if return_as_string:
                command = ""
                for el in node.parts:
                    if el.kind == 'word': 
                        command += el.word + ' '
                    elif el.kind == 'redirect': 
                        command +=  el.type + ' ' + el.output.word + ' '
                command = command[:-1]  # remove final space because thats wrong
                if command not in saved_command_dictionary[node.parts[0].word]: 
                    saved_command_dictionary[node.parts[0].word] += [command]
            else:
                if node not in saved_command_dictionary[node.parts[0].word]:  # This might not actually identify uniqueness. Need to check & update bashlex
                    saved_command_dictionary[node.parts[0].word] += [node]  
    return saved_command_dictionary


def return_commands_from_variable_delcaraction(node):
    """(node) strips the commands from a variable declaration if its of the form a=$(some command)\
	returns a list of any commands found in the node"""
    if type(node) is not bashlex.ast.node: raise ValueError('node must be a bashlex.ast.node')

    commands = []
    assignments = return_paths_to_node_type(node, [], [], 'assignment')
    for assignment in assignments:
        command_substitutions = return_paths_to_node_type(assignment.node, [], [], 'commandsubstitution')
        for substitution in command_substitutions:
            commands += return_commands_from_command_substitutions(substitution.node)

    return commands


# Add function to pull all commands executed via a command substitution
def return_commands_from_command_substitutions(node):
    if type(node) is not bashlex.ast.node: raise ValueError('node must be a bashlex.ast.node')
    commands = []
    command_substitutions = return_paths_to_node_type(node, [], [], 'commandsubstitution')
    for substitution in command_substitutions:
        commands += [substitution.node.command]
    return commands