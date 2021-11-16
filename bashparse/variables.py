from bashparse.path_variable import path_variable
from bashparse.ast import return_paths_to_node_type, return_variable_paths, shift_ast_pos
import bashlex, copy


def update_trees_pos(node, path_to_update, delta):
    # NOTE: Pass by reference
    # This function follows the path and replaces the pos of every node it touches
    # The nodes to the right of the nodes on the path, will also have their locations changed
    # We pass path = [-1] to the nodes to the right and then to all of its children
    # This causes the change to propagate through all affected nodes
    if type(node) is not bashlex.ast.node: raise ValueError('node must be a bashlex.ast.node')
    if type(path_to_update) is not list: raise ValueError('path_to_update must be a list')
    if type(delta) is not int: raise ValueError('length_new_value must be an int')

    if path_to_update != [-1] and len(path_to_update):
        traversed = False
        orig_node = node
        while not traversed:
            if hasattr(node, 'parts'): 
                traversed = True
                node.pos = ( node.pos[0], node.pos[1] + delta )
                if len(node.parts):
                    node = node.parts[path_to_update[0]]
            elif hasattr(node, 'list'):
                traversed = True
                node.pos = ( node.pos[0], node.pos[1] + delta )
                if len(node.list):
                    node = node.list[path_to_update[0]]
            elif hasattr(node, 'command'):  # some nodes are just pass through nodes
                    node.pos = ( node.pos[0], node.pos[1] + delta )
                    node = node.command
                    orig_node = orig_node.command
            elif hasattr(node, 'output'):   # some nodes are just pass through nodes
                    node.pos = ( node.pos[0], node.pos[1] + delta )
                    node = node.output
                    orig_node = orig_node.output
        update_trees_pos(node, path_to_update[1:], delta)
        if hasattr(orig_node, 'parts'):
            for i in range(path_to_update[0] + 1, len(orig_node.parts)):
                shift_ast_pos(orig_node.parts[i], delta)
        if hasattr(orig_node, 'list'):
            for i in range(path_to_update[0]+1, len(orig_node.list)):
                shift_ast_pos(orig_node.list[i], delta)


def update_command_substitution(node):
    if type(node) is not bashlex.ast.node: raise ValueError('node must be a bashlex.ast.node')
    command_substitutions_paths = reversed(return_paths_to_node_type(node, 'commandsubstitution'))

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
            if hasattr(command_node, 'list'):
                command_node = command_node.list[point]
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
    

def replace_variables_using_paths(nodes, paths, var_list):
    if type(paths) is not list: paths = [paths]

    for el in paths:
        if type(el) is not path_variable: raise ValueError('the elements of the paths list must be ints')
    if type(var_list) is not dict: raise ValueError('var_list must be a dictionary')
    for node in nodes:
        if type(node) is not bashlex.ast.node: raise ValueError('nodes must be of type bashlex.ast.node')
        
    to_return = []
    for node in nodes:
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
                            if hasattr(node_to_replace, 'command'):  # some nodes are just pass through nodes
                                if node_to_replace.kind == 'commandsubstitution':  
                                    # only trigger update command sub if the variable replacement is nested somewhere inside a commandsubstitution node
                                    has_commandsubstitution = True
                                node_one_up = node_to_replace
                                node_to_replace = node_to_replace.command
                            if hasattr(node_to_replace, 'output'):   # some nodes are just pass through nodes
                                node_one_up = node_to_replace
                                node_to_replace = node_to_replace.output
                            if hasattr(node_to_replace, 'parts'): 
                                node_one_up = node_to_replace
                                node_to_replace = node_to_replace.parts[point]
                            if hasattr(node_to_replace, 'list'):
                                node_one_up = node_to_replace
                                node_to_replace = node_to_replace.list[point]
                            
                        # Find the location in the string that we actually need to replace and replace with with the var
                        variable_start = node_to_replace.pos[0] - node_one_up.pos[0]
                        variable_end = node_to_replace.pos[1] - node_one_up.pos[0]
                        # The above isn't technically correct, as there could be quotes which wouldn't be saved but affect the location so we adopt this as a starting point
                        # And use the following alg to determine the real starting point
                        found_var = node_one_up.word[variable_start:variable_end] == '$'+path_val.node.value
                        while not found_var and variable_start >= 0:
                            variable_start -= 1
                            variable_end -= 1
                            found_var = node_one_up.word[variable_start:variable_end] == '$'+path_val.node.value
                        if  not found_var:
                            variable_start = node_to_replace.pos[0] - node_one_up.pos[0]
                            variable_end = node_to_replace.pos[1] - node_one_up.pos[0]
                        while not found_var and variable_end < len(node_one_up.word):
                            variable_start += 1
                            variable_end += 1
                            found_var = node_one_up.word[variable_start:variable_end] == '$'+path_val.node.value
                        node_one_up.word = node_one_up.word[:variable_start] + path_val.value[j] + node_one_up.word[variable_end:]
                        if has_commandsubstitution:
                            update_command_substitution(node=replaced_trees[(i*len(path_val.value)) + j])
                        update_trees_pos(node=replaced_trees[(i*len(path_val.value)) + j], path_to_update=path_val.path, delta= len(path_val.value[j]) -( variable_end - variable_start))
                        del node_one_up.parts[path_val.path[-1]]  # Remove parameter node because it has been replaced
        to_return += replaced_trees
    return to_return


def substitute_variables(nodes, var_list):
    if type(nodes) is not list: nodes = [nodes]
    for node in nodes: 
        if type(node) is not bashlex.ast.node: raise ValueError('nodes must be a bashlex.ast.node')
    if type(var_list) is not dict: raise ValueError('var_list must be a dictionary')

    to_return = []
    for node_in in nodes:
        
        replaced_nodes = []
        node = copy.deepcopy(node_in)  # This maintains the integrity of the node passed in cause its passed by ref
        
        if node.kind != 'pipeline' and node.kind != 'operator' and node.kind != 'word' and node.kind != 'reservedword':
            # Strip all the assignments from the tree. Sorted in order they appear
            assignment_nodes = return_paths_to_node_type(node, 'assignment')
            # Strip all the variables used from the tree. Sorted in order they appear
            variable_nodes = return_variable_paths(node)
            # Strip all the for loops used from the tree. Sorted in order they appear
            for_nodes = return_paths_to_node_type(node, 'for')
            # Interleave the assignments and variables so that we have an array of assignments and variable uses in the order that they appear
            assignment_variables_in_order = []
            while(len(assignment_nodes) and len(variable_nodes)):
                # Find the shorter path
                length = len(assignment_nodes[0].path) if len(assignment_nodes[0].path) < len(variable_nodes[0].path) else len(variable_nodes[0].path)
                assignment_moved = False
                variable_moved = False
                for i in range(0, length):
                    if assignment_nodes[0].path[i] < variable_nodes[0].path[i]:
                        assignment_variables_in_order += [assignment_nodes[0]]
                        assignment_moved = True
                        break
                    elif assignment_nodes[0].path[i] > variable_nodes[0].path[i]:
                        assignment_variables_in_order += [variable_nodes[0]]
                        variable_moved = True
                        break
                if assignment_moved: assignment_nodes = assignment_nodes[1:]
                elif variable_moved: variable_nodes = variable_nodes[1:]
                else:
                    if len(assignment_nodes[0].path) < len(variable_nodes[0].path):
                        assignment_variables_in_order += [ variable_nodes[0], assignment_nodes[0] ]
                    elif len(variable_nodes[0].path) < len(assignment_nodes[0].path):
                        assignment_nodes = assignment_nodes[1:]
                    else:
                        assignment_variables_in_order += [ variable_nodes[0], assignment_nodes[0] ]
                    assignment_nodes = assignment_nodes[1:]
                    variable_nodes = variable_nodes[1:]
            assignment_variables_in_order += variable_nodes
            assignment_variables_in_order += assignment_nodes

            action_paths = []
            while(len(assignment_variables_in_order) and len(for_nodes)):
                # Find the shorter path
                length = len(assignment_variables_in_order[0].path) if len(assignment_variables_in_order[0].path) < len(for_nodes[0].path) else len(for_nodes[0].path)
                assignment_moved = False
                for_moved = False
                for i in range(0, length):
                    if assignment_variables_in_order[0].path[i] < for_nodes[0].path[i]:
                        action_paths += [assignment_variables_in_order[0]]
                        assignment_moved = True
                        break
                    elif assignment_variables_in_order[0].path[i] > for_nodes[0].path[i]:
                        assignment_variables_in_order += [for_nodes[0]]
                        for_moved = True
                        break
                if assignment_moved: assignment_variables_in_order = assignment_variables_in_order[1:]
                elif for_moved: for_nodes = for_nodes[1:]
                else:
                    if len(assignment_variables_in_order[0].path) < len(for_nodes[0].path):
                        action_paths += [ assignment_variables_in_order[0], for_nodes[0] ]
                    elif len(for_nodes[0].path) < len(assignment_variables_in_order[0].path):
                        action_paths += [ for_nodes[0], assignment_variables_in_order[0] ]
                assignment_variables_in_order = assignment_variables_in_order[1:]
                for_nodes = for_nodes[1:]
            action_paths += assignment_variables_in_order
            action_paths += for_nodes

            # Now we have assignments and replacements in the order that they occur
            replaced_nodes = [ node ]
            # for action_path in action_paths:
            i = 0
            while i < len(action_paths):
                if action_paths[i].node.kind == 'assignment':
                    var_list = update_variable_list_with_node(action_paths[i].node, var_list)
                    i += 1
                elif action_paths[i].node.kind == 'parameter':
                    paths = []
                    while i < len(action_paths) and action_paths[i].node.kind == 'parameter':
                        paths += [ action_paths[i] ]
                        i += 1
                    replaced_nodes = replace_variables_using_paths(replaced_nodes, paths, var_list)
                elif action_paths[i].node.kind == 'for':
                    var_list = update_var_list_with_for_loop(action_paths[i].node, var_list)
                    paths = []
                    
                    while i < len(action_paths):
                        if action_paths[i].path[0:len(action_paths[i].path)] == action_paths[i].path:
                            paths += [ action_paths[i] ]
                            i += 1
                    replaced_nodes = replace_variables_using_paths(replaced_nodes, paths[1:], var_list)
                    # replaced_nodes = replace_variables_using_paths(replaced_nodes, action_paths[i], var_list)
                    i += 1

        if len(replaced_nodes) == 0: return [copy.deepcopy(node)]
        to_return += replaced_nodes
    return to_return


def add_variable_to_list(var_list, name, value): 
    """(variable dict, name, value) Adds the corresponding name and value to dictionary. Planning on people misuing the dictionary
	returns the updated variable dict"""

    if type(var_list) is not dict: raise ValueError('var_list must be a dictionary')
    name = str(name)
    
    # We are only going to save things as arrays. This makes the unwrapping/replacing in the node structure easier
    if value is not None:
        if type(value) is not list: value = [str(value)]
        if name in var_list:  # The following section allows for if redifinitions without any problems. Covers more cases
            # Convert all values to strings because they should be
            for val in value:
                if str(val) not in var_list[name]:
                    var_list[name] = var_list[name] + [str(val)]
        else: 
            var_list[name] = [str(x) for x in value]  # typecast every element to string just in case
    return var_list


def update_variable_list_with_node(nodes, var_list):
    """(node, variable dict) strips any variables out of ast and saves them to variable list. Also saves mv x y for later use (could be separated)
	returns an updated variable dict"""
    if type(nodes) is not list: nodes = [nodes]
    for node in nodes:
        if type(node) is not bashlex.ast.node: raise ValueError('node must be a bashlex.ast.node')
    if type(var_list) is not dict: raise ValueError('var_list must be dictionary')
    for node in nodes:
        if node.kind == 'assignment':
            name, value = node.word.split('=', maxsplit=1)
            var_list = add_variable_to_list(var_list, name, value)

        if hasattr(node, 'parts') and len(node.parts):
            if node.parts[0].kind == 'assignment':
                name, value = node.parts[0].word.split('=', maxsplit=1)
                var_list = add_variable_to_list(var_list, name, value)
            elif hasattr(node.parts[0], 'word') and node.parts[0].word == 'for':
                var_list = update_var_list_with_for_loop(node, var_list)

    return var_list


def update_var_list_with_for_loop(nodes, var_list):
    # Verify that the node is a for loop of the format: for x in y
    if type(nodes) is not list: nodes = [nodes]
    for el in nodes:
        if type(el) is not bashlex.ast.node: raise ValueError('nodes must be a bashlex.ast.node')
    for itr in nodes:
        paths_to_for_loops = return_paths_to_node_type(itr, 'for')
        for path in paths_to_for_loops:
            node = path.node
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
                    
                var_list = add_variable_to_list(var_list, name, variable_value)

    return var_list


def find_and_replace_variables(nodes, var_list = {}):
    return substitute_variables(nodes, var_list)


