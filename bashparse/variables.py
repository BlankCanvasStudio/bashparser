import bashparse.ast as bpast
from bashparse.ast import NodeVisitor
from bashparse.ast import CONT, DONT_DESCEND
import bashlex, copy, re

def replace_variables(node, var_list, var_list_order = []):

    def find_variable_location(node, parent, variable_name):
        variable_start = node.pos[0] - parent.pos[0] if node.pos[0] - parent.pos[0] >= 0 else 0
        variable_end = variable_start + len(variable_name) + 1
        inc_amt = 0

        while parent.word[variable_start:variable_end] != '$'+variable_name:    # locate the $ in the word
            # This will cause you bugs
            inc_amt = (abs(inc_amt) + 1) * pow(-1, abs(inc_amt+1))
            variable_start = (variable_start + inc_amt) % (len(parent.word) + 1)
            variable_end = (variable_end + inc_amt) % (len(parent.word) + 1)
        
        return variable_start, variable_end

    def adjust_node_deltas(vstr, j):
        tmp_n = vstr.at_path(vstr.nodes[j], vstr.path)
        start = tmp_n.pos[0] + vstr.accum_deltas[j] if tmp_n.pos[0] + vstr.accum_deltas[j] > 0 else 0
        tmp_n.pos = ( start, tmp_n.pos[1] + vstr.accum_deltas[j])

    def apply_fn(node, vstr, var_list):

        if node.kind == 'parameter' and node.value in vstr.replaced_variables:
            """ child num of the param node is last el in path """
            new_nodes = []
            for node_to_trim in vstr.nodes:
                new_nodes += [ vstr.remove(node_to_trim, copy.copy(vstr.path)) ]
            vstr.nodes = new_nodes

            name_to_replace = node.value
            name_with_data = name_to_replace
            if type(var_list[name_to_replace][0]) == str and var_list[name_to_replace][0][:len('for_loop$')] == 'for_loop$':   # lmao
                name_with_data = var_list[name_to_replace][0].split('$')[1] 

            division_width = len(vstr.nodes) // len(var_list[name_with_data])
            for i, value in enumerate(var_list[name_with_data]):
                for j in range(i*division_width, (i+1)*division_width):
                    delta = 0
                    if type(value) is str:
                        delta = len(value) - (len('$') + len(name_to_replace))                  # Change in text len due to value sub. ie delta = new_len - old_len
                        vstr.nodes[j] = bpast.expand_ast_along_path(vstr.nodes[j], vstr.path[:-1], delta)
                    elif type(value) is bashlex.ast.node:
                        parent = vstr.at_path(vstr.root, vstr.path[:-1])

                        delta = (value.pos[1] - value.pos[0]) - (parent.pos[1] - parent.pos[0])    # (New node len) - (Old node len) where old node is parent being repalced 
                        vstr.nodes[j] = bpast.expand_ast_along_path(vstr.nodes[j], vstr.path[:-2], delta)

                    else: 
                        raise ValueError("Error! Value in var_list is not str or bashlex.ast.node and replace_variables was called.")
                    
                    vstr.accum_deltas[j] += delta

        else:
            replaced = False 
            if node.kind in vstr.contains_variable_text:            
                var_name_re = re.compile("(?<=\$)\w*\b")
                var_names = re.findall(r'(?<=\$)\w*\b', node.word)      # Simple regex and drops 

                for name_to_replace in var_names: 

                    if name_to_replace in var_list:

                        name_with_data = name_to_replace    # if you do for a in $n, we need to repalce $n as if it was a. This separates the data from the name

                        if type(var_list[name_to_replace][0]) == str and var_list[name_to_replace][0][:len('for_loop$')] == 'for_loop$':   # lmao
                            name_with_data = var_list[name_to_replace][0].split('$')[1] 
                        
                        if name_with_data not in vstr.replaced_variables:
                            new_nodes = []
                            new_accum_deltas = []

                            for i in range(0, len(vstr.nodes)):
                                for j in range(0, len(var_list[name_with_data])):
                                    new_nodes += [ copy.deepcopy(vstr.nodes[i]) ]
                                    new_accum_deltas += [ copy.deepcopy(vstr.accum_deltas[i]) ]

                            vstr.nodes = new_nodes
                            vstr.accum_deltas = new_accum_deltas
                            vstr.replaced_variables[name_with_data] = [len(vstr.replaced_variables)]
                            vstr.variable_replacement_order += [name_with_data]                             
                                # We need to track the replacement order so we can figure out which sections of the tree have which value for each variable
                        if name_to_replace not in vstr.replaced_variables:
                            vstr.replaced_variables[name_to_replace] = [len(vstr.replaced_variables)]

                        division_width = len(vstr.nodes) // len(var_list[vstr.variable_replacement_order[0]])           # division width tells use how many nodes in a row have same value
                        i = 0
                        while vstr.variable_replacement_order[i] != name_with_data:
                            i += 1
                            division_width = division_width // len(var_list[vstr.variable_replacement_order[i]])

                        values = var_list[name_with_data]

                        iteration_num = len(vstr.nodes) // (division_width)//(len(values))

                        for h in range(0, iteration_num):
                            for i, value in enumerate(values):
                                for j in range(0, division_width):

                                    index = (h*iteration_num) + (i*division_width) + j
                                    
                                    if type(value) is str:
                                        # regex to update the current node
                                        pattern = r'\$' + re.escape(name_to_replace) + r'\b'
                                        jth_node = vstr.at_path(vstr.nodes[index], vstr.path)
                                        jth_node.word = re.sub(pattern, value, jth_node.word)
                                    elif type(value) is bashlex.ast.node: 
                                        vstr.nodes[index] = vstr.replace_node(vstr.nodes[index], vstr.path, value)
                                    else: 
                                        raise ValueError("Error! Variable replacement value wasn't a str or node. bashparse.variables.replace_variables")

            for j in range(0, len(vstr.nodes)):
                    try:
                        adjust_node_deltas(vstr, j)
                    except Exception as e:
                        print('Error in adjusting node deltas in replace_variables')
                        print('Exception: ', e)
                        print('current node: ', node.dump())
                        print('path: ', vstr.path)
                        print('root: ', vstr.root.dump())
                        print('\n\n\n')

        return CONT

    vstr = NodeVisitor(node)
    vstr.apply(apply_fn, vstr, var_list)
    return vstr.nodes


def substitute_variables(nodes, var_list):
    if type(nodes) is not list: nodes = [nodes]
    for node in nodes:
        if type(node) is not bashlex.ast.node: raise ValueError('nodes must be of type bashparse.node')
    if type(var_list) is not dict: raise ValueError('var_list must be of type dict')
    to_return = []
    
    for node in nodes:
        var_list = update_variable_list_with_node(node, var_list)
        to_return += replace_variables(node, var_list)
    return to_return



def add_variable_to_list(var_list, name, value): 
    """ (variable dict, name, value) Adds the corresponding name and value to dictionary. Planning on people misuing the dictionary
	returns the updated variable dict """

    if type(var_list) is not dict: raise ValueError('var_list must be a dictionary')
    if value is None: return
    name = str(name)
    # We are only going to save things as arrays. This makes the unwrapping/replacing in the node structure easier
    if type(value) is not list: value = [str(value)]
    
    if name in var_list:  # The following section allows for if redifinitions without any problems. Covers more cases
        # Convert all values to strings because they should be
        for val in value:
            if str(val) not in var_list[name]:
                var_list[name] += [str(val)]
    else: 
        var_list[name] = [str(x) for x in value]  # typecast every element to string just in case
    return var_list


def update_variable_list_with_node(node, var_list):
    """(node, variable dict) strips any variables out of ast and saves them to variable list. Also saves mv x y for later use (could be separated)
	returns an updated variable dict"""
    if type(node) is not bashlex.ast.node: raise ValueError('node must be a bashparse.node')
    if type(var_list) is not dict: raise ValueError('var_list must be dictionary')

    def apply_fn(node, var_list):
        if node.kind == 'assignment':
            name, value = node.word.split('=', maxsplit=1)
            var_list = add_variable_to_list(var_list, name, value)
        elif node.kind == 'for':
            var_list = update_var_list_with_for_loop(node, var_list)
        return CONT
    NodeVisitor(node).apply(apply_fn, var_list)
    return var_list


def update_var_list_with_for_loop(node, var_list):
    # This always returns properly
    # Verify that the node is a for loop of the format: for x in y
    if type(node) is not bashlex.ast.node: raise ValueError('nodes must be a bashparse.node')

    if ( hasattr(node, 'parts') and len(node.parts) >= 3 and  
            hasattr(node.parts[0], 'word') and node.parts[0].word == 'for' and 
            hasattr(node.parts[2], 'word') and node.parts[2].word == 'in'  ) :
        name = node.parts[1].word
        value_index = 3
        variable_value = []
        value_nodes = []
        while value_index < len(node.parts) and node.parts[value_index].word != ';' and node.parts[value_index].word !='do':
            """ Values can only be in word nodes so we check for variables, command siubsitutions, and any 
                nested options. We then convert it to its fully replaced form """
            if not len(node.parts[value_index].parts):
                variable_value += node.parts[value_index].word.split(' ')
            else:
                for part in node.parts[value_index].parts: 
                    if part.kind == 'parameter':
                        variable_value += [ 'for_loop$' + part.value ]
                    if part.kind == 'commandsubstitution':
                        value_nodes = substitute_variables(part, var_list)
                        for value_node in value_nodes: 
                            variable_value += [ str(NodeVisitor(value_node)) ]
            value_index += 1
        var_list = add_variable_to_list(var_list, name, variable_value)
    return var_list
