import bashlex, copy

def find_specific_commands(node:bashlex.ast.node, commands_looking_for:list, saved_command_dictionary:dict, return_as_string:bool):
    if node.kind == 'for' or node.kind == 'list' or node.kind == 'commandsubstitution':
        for part in node.parts:
            saved_command_dictionary = find_specific_commands(part, commands_looking_for, saved_command_dictionary, return_as_string)
    elif node.kind == 'command' and node.parts[0].word in commands_looking_for:
            if return_as_string:
                command = ""
                for el in node.parts:
                    if el.kind == 'word': 
                        command += el.word + ' '
                    elif el.kind == 'redirect': 
                        command +=  el.type + ' ' + el.output.word + ' '
                if command not in saved_command_dictionary[node.parts[0].word]: 
                    saved_command_dictionary[node.parts[0].word] += [command]
            else:
                if node not in saved_command_dictionary[node.parts[0].word]:  # This might not actually identify uniqueness. Need to check & update bashlex
                    saved_command_dictionary[node.parts[0].word] += [node]  
    return saved_command_dictionary

def return_commands_from_variable_delcaraction(node:bashlex.ast.node):
    commands =  []
    if node.kind == 'assignment':
        for part in node.parts:
            if part.kind == 'commandsubstitution': 
                commands += [copy.deepcopy(part.command)]
    if node.kind == 'command' and len(node.parts):
        for part in node.parts:
            commands += return_commands_from_variable_delcaraction(part)
    return commands