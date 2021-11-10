from bashparse.path_variable import path_variable
import bashlex, copy

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
    """(node, [], []) Return locs in ast where variables are. empty arrays cause recursion
    returns array of path_variable objects which are used to locate variables"""
    return return_paths_to_node_type(node, current_path, paths, 'parameter')


def update_trees_pos(node:bashlex.ast.node, path_to_update:list, length_new_value:int, length_old_value:int, name:str):
    # NOTE: Pass by reference
    # This function follows the path and replaces the pos of every node it touches
    # The nodes to the right of the nodes on the path, will also have their locations changed
    # We pass path = [-1] to the nodes to the right and then to all of its children
    # This causes the change to propagate through all affected nodes
    if path_to_update != [-1] and len(path_to_update):
        traversed = False
        orig_node = node
        while not traversed:
            if hasattr(node, 'parts'): 
                    traversed = True
                    node.pos = ( node.pos[0], node.pos[1] - length_old_value + length_new_value )
                    if len(node.parts):
                        node = node.parts[path_to_update[0]]
            elif hasattr(node, 'command'):  # some nodes are just pass through nodes
                    node.pos = ( node.pos[0], node.pos[1] - length_old_value + length_new_value )
                    node = node.command
                    orig_node = orig_node.command
            elif hasattr(node, 'output'):   # some nodes are just pass through nodes
                    node.pos = ( node.pos[0], node.pos[1] - length_old_value + length_new_value )
                    node = node.output
                    orig_node = orig_node.output
        update_trees_pos(node, path_to_update[1:], length_new_value, length_old_value, name)

        if hasattr(orig_node, 'parts'):
            for i in range(path_to_update[0] + 1, len(orig_node.parts)):
                update_trees_pos(orig_node.parts[i], [-1], length_new_value, length_old_value, name)
    
    if path_to_update == [-1]:
        node.pos = ( node.pos[0] - length_old_value + length_new_value, node.pos[1] - length_old_value + length_new_value)
        if hasattr(node, 'command'):  # some nodes are just pass through nodes
            node = node.command
        if hasattr(node, 'output'):   # some nodes are just pass through nodes
            node = node.output
        if hasattr(node, 'parts'):
            for part in node.parts:
                update_trees_pos(part, [-1], length_new_value, length_old_value, name)


def shift_tree_pos(node:bashlex.ast.node, shift_amount):
    node.pos = (node.pos[0] + shift_amount, node.pos[1] + shift_amount)
    if hasattr(node, 'parts'): 
        for part in node.parts:
            shift_tree_pos(part, shift_amount) 
    if hasattr(node, 'command'):  # some nodes are just pass through nodes
        shift_tree_pos(node.command, shift_amount)
    if hasattr(node, 'output'):   # some nodes are just pass through nodes
        shift_tree_pos(node.output, shift_amount)
    return node


def shift_tree_pos_to_start(node:bashlex.ast.node):
    return shift_tree_pos(node, node.pos[1])  # EZPZ


def update_command_substitution(node:bashlex.ast.node):
    command_substitutions_paths = return_paths_to_node_type(node, [], [], 'commandsubstitution')

    for path_var in command_substitutions_paths:
        command_node = node
        for point in path_var.path:
            # The commandsubstitution node needs to be passed through and doesn't contain the word that needs to be updated
            # The node of which command substitution is a part needs to be updated, so we need to find both the commandsubstitution
                # node and the node above the commandsubstitution node w
                # which contains the word to be updated
            node_to_update = command_node
            commandsubstitution_node = command_node
            if hasattr(command_node, 'parts'): 
                command_node = command_node.parts[point]
            if hasattr(command_node, 'command'):  # some nodes are just pass through nodes
                commandsubstitution_node = command_node  # This needs to be updated here cause we don't wanna only save if we change via parts
                command_node = command_node.command
            if hasattr(command_node, 'output'):   # some nodes are just pass through nodes
                commandsubstitution_node = command_node
                command_node = command_node.output

        # Create the new command string to inject
        new_command_string = "$("
        for part in command_node.parts: new_command_string += part.word + ' '
        new_command_string = new_command_string[:-1] + ')'  # Need to remove the final space cause thats wrong
        # Get the indexes of the command we are updating. Needs to be replative to the start of the word node we are repalcing in
        substitution_start = commandsubstitution_node.pos[0] - node_to_update.pos[0]
        substitution_end = commandsubstitution_node.pos[1] - node_to_update.pos[0]
        # Lets do that update 
        node_to_update.word = node_to_update.word[:substitution_start] + new_command_string + node_to_update.word[substitution_end:]
    
    
def replace_variables(node:bashlex.ast.node, paths:list, var_list:dict):
    # The name of the variable is store in node.value
    unique_names = []
    unique_trees_needed = 1
    # Find how many unique trees we need to fit the entire replaced variable space
    for path_val in paths:
        if path_val.node.value in var_list:  # I decided to do the iteration here cause I need to count unique entries any way so I might as well do it in one step
            if path_val.node.value not in unique_names:
                unique_names += [path_val.node.value]
                if type(var_list[path_val.node.value]) is not list: var_list[path_val.node.value] = [ var_list[path_val.node.value] ]  # For safety sake. I made this mistake
                unique_trees_needed *= len(var_list[path_val.node.value])
            path_val.value = var_list[path_val.node.value]
    
    replaced_trees = []
    for i in range(0, unique_trees_needed): replaced_trees += [copy.deepcopy(node)]  # save a bunch of unreplaced trees to be replaced
    
    # Iterate over every location we need to replace. 
    # We divide the number of trees by the number of unique entries we need to replace
    # This returns us the number of areas where unique variables need to be replaced
    # Then we replace these locations
    # If there are 10 unique trees and $n=[1,2] then in the first 5 trees $n will be replaced with 1 and in the next 5 with 2
    for path_val in paths:  # We don't need to worry about replacing a given var all at once as long as it replaces the same every time we encounter it
        if path_val.value:  # Only replace if there is something to replace. $1 would have no value but shouldn't be deleted
            num_divisions = unique_trees_needed // len(path_val.value)  # Always int cause its a factor
            for i in range(0, num_divisions):
                for j in range(0, len(path_val.value)):
                    node_to_replace = replaced_trees[(i*len(path_val.value)) + j]  # Iterates wonderfully, looks gross
                    # ^ Set the tree to the root node. We will dive to actual node from there (cause thats where paths are found from)
                    has_commandsubstitution = False  # I hate this implementation. Will improve
                    for point in path_val.path:  # Dive down tree until we get to node we actually need to replace
                        node_one_up = node_to_replace
                        if hasattr(node_to_replace, 'parts'): 
                            node_to_replace = node_to_replace.parts[point]
                        if hasattr(node_to_replace, 'command'):  # some nodes are just pass through nodes
                            if node_to_replace.kind == 'commandsubstitution':  
                                # only trigger update command sub if the variable replacement is nested somewhere inside a commandsubstitution node
                                has_commandsubstitution = True
                            node_to_replace = node_to_replace.command
                        if hasattr(node_to_replace, 'output'):   # some nodes are just pass through nodes
                            node_to_replace = node_to_replace.output
                    # Find the location in the string that we actually need to replace and replace with with the var
                    variable_start = node_to_replace.pos[0] - node_one_up.pos[0]
                    variable_end = node_to_replace.pos[1] - node_one_up.pos[0]
                    node_one_up.word = node_one_up.word[:variable_start] + path_val.value[j] + node_one_up.word[variable_end:]
                    if has_commandsubstitution:
                        update_command_substitution(node=replaced_trees[(i*len(path_val.value)) + j])
                    print('replaced tree: ', replaced_trees[(i*len(path_val.value)) + j])
                    update_trees_pos(node=replaced_trees[(i*len(path_val.value)) + j], path_to_update=path_val.path[:-1], length_new_value=len(path_val.value[j]), length_old_value=variable_end - variable_start, name=path_val.node.value)
                    del node_one_up.parts[path_val.path[-1]]  # Remove parameter node because it has been replaced
    return replaced_trees


def substitute_variables(node:bashlex.ast.node, var_list:dict):

    replaced_nodes = []

    if node.kind == 'list':
        for part in node.parts:
            replaced_nodes += substitute_variables(part, var_list)

    elif node.kind == 'compound':
        for part in node.list:
            replaced_nodes += substitute_variables(part, var_list)
    
    elif node.kind == 'command':
        paths = return_variable_paths(node, [], [])
        new_nodes = replace_variables(node, paths, var_list)
        replaced_nodes += new_nodes  
    
    elif node.kind == 'for': 
        var_list = update_var_list_with_for_loop(node, var_list)  # This is so that we can use the for loop iterator to replace stuff later
        paths = return_variable_paths(node, [], [])
        replaced_nodes += replace_variables(node, paths, var_list) 

    elif node.kind != 'pipeline' and node.kind != 'operator' and node.kind != 'word':
        print("node was recieved that we don't have implementation to parse. Kind: ", node.kind)
        print('node: ', node)

    if len(replaced_nodes) == 0: return [node]
    return replaced_nodes


def add_var_to_var_list(var_list:dict, name:str, value:list): 
    # We are only going to save things as arrays. This makes the unwrapping/replacing in the node structure easier
    if value is not None:
        if name in var_list:  # The following section allows for if redifinitions without any problems. Covers more cases
            if type(value) is not list: value = [value]
            for val in value:
                if val not in var_list[name]:
                    var_list[name] = var_list[name] + [val]
        else: 
            if type(value) is not list: var_list[name] = [value]
            else: var_list[name] = value
    return var_list


def update_variable_list(node:bashlex.ast.node, var_list:dict):

    if hasattr(node, 'parts') and len(node.parts):
        if node.parts[0].kind == 'assignment':
            name, value = node.parts[0].word.split('=', maxsplit=1)
            var_list = add_var_to_var_list(var_list, name, value)
        elif node.parts[0].kind == 'word' and node.parts[0].word == 'mv':
            # Move index to past the flagss
            non_flag_base = 1
            while node.parts[non_flag_base].word[0] == '-':  # Remove any flags
                non_flag_base = non_flag_base + 1
            # As long as indexes are still in bounds
            if non_flag_base + 1 < len(node.parts):
                orig_cmd = node.parts[non_flag_base]
                mvd_cmd = node.parts[non_flag_base + 1]
                    # Generic remove everything before the '/' 
                    # IDK about readability when I can flex this hard
                if '/' in orig_cmd[:orig_cmd.index(' ')]: orig_cmd = orig_cmd[orig_cmd[:orig_cmd.index(' ')].rfind('/') + 1:]
                if '/' in mvd_cmd[:mvd_cmd.index(' ')]: mvd_cmd = mvd_cmd[mvd_cmd[:mvd_cmd.index(' ')].rfind('/') + 1:]

                if orig_cmd in var_list['mv_list']:  # This is to get around nesting
                    # If the cmd we are moving in already in the mv_list then it isn't the orginial cmd
                    # This intermediate command is useless so we save the one 1 level up. This meaqns the cmd
                    # 1 level up is always the original cmd, thus this gets the original cmd. Works for infinite
                    # depth nesting cause its done piecewise
                    orig_cmd = var_list['mv_list'][orig_cmd]
                var_list['mv_list'][mvd_cmd] = orig_cmd 
        elif hasattr(node.parts[0], 'word') and node.parts[0].word == 'for':
            var_list = update_var_list_with_for_loop(node, var_list)

    return var_list


def update_var_list_with_for_loop(node:bashlex.ast.node, var_list:dict):
    # Verify that the node is a for loop of the format: for x in y
    if ( hasattr(node, 'parts') and len(node.parts) >= 3 and  
        hasattr(node.parts[0], 'word') and node.parts[0].word == 'for' and 
        hasattr(node.parts[2], 'word') and node.parts[2].word == 'in'  ) :
            
        name = node.parts[1].word
        value_node = node.parts[3]
        variable_value = [value_node.word]  # Give it a default value and change if necessary

        if len(value_node.parts) and value_node.parts[0].kind == 'parameter' and value_node.parts[0].value in var_list:  
            # This means its a variable declaration and the variable value exists, so we are gonna repalce it 
            # If the value doesn't exist we leave it as $var. Useful for things like $1
            variable_value = var_list[value_node.parts[0].value]
        
        if len(variable_value) == 1 and type(variable_value[0]) == str and ' ' in variable_value[0]:
            if len(value_node.parts):  # Theres a chance its a command substitution, which means splitting on spaces is bad so we verify it isn't one
                if value_node.parts[0].kind == 'commandsubstitution': 
                    value_node = substitute_variables(value_node, var_list)
                    variable_value = [value_node[0].word]
                else:
                    variable_value = variable_value[0].split(' ') 
            else:
                # If there is a single value, which contains spaces and isn't a command substitution then bash is going to interpret this as an array
                variable_value = variable_value[0].split(' ') 
            
        var_list = add_var_to_var_list(var_list, name, variable_value)

    return var_list


