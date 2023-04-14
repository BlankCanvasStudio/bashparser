#!/bin/python3
import bashparser.ast
from bashparser.ast import NodeVisitor, CONT
import bashlex, copy, re


def replace_variables(nodes, var_list, replace_blanks=False):
    """ Takes a node, var list. Replaces all the instances of variables found in the var_list
        with their corresponding value via regex. var_list IS NOT UPDATED WITH VALUES IN NODE. 
        USE substitute_variables FOR THAT FUNCITONALITY. The identification of a variable is done via the 
        presence of a parameter node, thus is none are present, nothing will be replaced, even if a $name 
        is present in one of the nodes (ie only replace with valid bashlex nodes). The parameter nodes are removed
        if the value is replace, or kept if not. This means the nodes returned are all valid bashlex nodes. 
        This function also properly shifts the ast to account for any replacements, meaning you shouldn't be able
        to tell if the tree has been replaced or was generated directly from the text. You're welcome, it was hell  """

    if type(nodes) is not list: nodes = [ nodes ]
    for node in nodes:
        if type(node) is not bashlex.ast.node: raise ValueError('Error! bashparser.variables.replace_variables(node != bashlex.ast.node)')
    if type(var_list) is not dict: raise ValueError('Error! bashparser.variables.replace_variables(var_list != dict)')

    def gen_new_trees(vstr, name):
        """ If the variable has multiple values and the variable has not been encountered yet, 
            then the nodes must be replicated to allow for these new divergent execution paths 
            to be accunted for """
        if name in vstr.variable_replacement_order: return
        new_nodes = []
        new_accum_deltas = []

        for i in range(0, len(vstr.nodes)):
            for j in range(0, len(var_list[name])):
                new_nodes += [ copy.deepcopy(vstr.nodes[i]) ]
                new_accum_deltas += [ copy.deepcopy(vstr.accum_deltas[i]) ]

        vstr.nodes = new_nodes
        vstr.accum_deltas = new_accum_deltas
        vstr.variable_replacement_order.add(name)


    def note_param_for_removal(vstr, name, var_list):
        """ Note that we want to remove the parameter if it is a string regex
            if you did a node substitution then a parameter removal is incorrect. 
            Thus you shouldn't note it for removal """
        if type(var_list[name][0]) is not str: return
        vstr.params_for_removal += [ copy.deepcopy(vstr.path) ]


    def replace_value(vstr, name, var_list):
        """ This function actually replaces the variable at the path specified in vstr with the name $name
            and saves all the replacements back to vstr.nodes """

        """ Calculating replacement_width. replacement_width is the number of vstr.nodes in a row which 
            contain the same value for the variable $name. If there is only 1 variable being replaced then 
            replacement_width = 1. If its 2 nested for loops, with each iterator having 2 values, then the 
            most nested variable will have a replacement_width of 1 while the top most will have a 
            replacement_width of 2. I hope that makes sense """
        replacement_width = len(vstr.nodes)
        for el in vstr.variable_replacement_order:
            replacement_width //= len(var_list[el])
            if el == name: break

        """ h is used when the number of nodes is larger than the number of values 
            then you need to loop x times where x=itr_num and x*len(values) = len(vstr.nodes) """        
        factor = (len(var_list[name]) * replacement_width)
        itr_num = len(vstr.nodes) // factor

        for h in range(0, itr_num):
            for i, value in enumerate(var_list[name]):     # By this point the number of nodes will have factor of num of values
                for j in range(0, replacement_width):      # Indexing scheme is:  
                    nodes_index = (h * factor) + (i * replacement_width) + j

                    if type(value) is str:
                        pattern = r'\$' + re.escape(name) + r'\b'
                        jth_node = vstr.at_path(vstr.nodes[nodes_index], copy.copy(vstr.path[:-1]))
                        jth_node.word = re.sub(pattern, value, jth_node.word)
                        delta = len(value) - (len('$') + len(name))                  # Change in text len due to value sub. ie delta = new_len - old_len
                        vstr.nodes[nodes_index] = bashparser.ast.expand_ast_along_path(vstr.nodes[nodes_index], copy.copy(vstr.path[:-1]), delta)
                        vstr.nodes[nodes_index] = bashparser.ast.shift_ast_right_of_path(vstr.nodes[nodes_index], copy.copy(vstr.path[:-1]), delta)
                    elif type(value) is bashlex.ast.node: 
                        vstr.nodes[nodes_index] = vstr.swap_node(root=vstr.nodes[nodes_index], path=copy.copy(vstr.path[:-1]), child=value)
                    else: 
                        raise ValueError("Error! Variable replacement value wasn't a str or node. bashparser.variables.replace_variables")


    def apply_fn(node, vstr, var_list, replace_blanks=False):
        """ This function only works on parameter nodes in the tree. If there is no parameter 
            then the value is assumed to be a string or escaped in some capacity. Only replace
            the tree with valid bashlex nodes """
        if node.kind != 'parameter': return CONT
        
        """ If you set equality to a variable that doesn't exist, its a blank value according to bash.
            So we insert a blank value into the variable list it works just fine. Definitely a hacky workaround 
            But it hasn't created any bugs yet """
        if replace_blanks and node.value not in var_list: var_list[node.value] = [ '' ]    
        if not replace_blanks and node.value not in var_list: return CONT

        name = node.value

        """ If this is the for loop iterator then replace it as a single string """
        gparent = vstr.at_path(vstr.root, vstr.path[:-2])
        if gparent is not None and gparent.kind == 'for': 
            tmp_var_list = copy.deepcopy(var_list)
            tmp_var_list[name] = [' '.join(var_list[name])]
            replace_value(vstr, name, tmp_var_list)      # Cheeky work around
            note_param_for_removal(vstr, name, tmp_var_list)
            return CONT

        """ Create new trees if variable hasn't already been replaced """
        gen_new_trees(vstr, name)

        """ child num of the param node is last el in path. So we remove the parameter nodes """
        note_param_for_removal(vstr, name, var_list)

        """ replace the value in the node """
        replace_value(vstr, name, var_list)

        return CONT

    to_return = []
    for node in nodes:
        vstr = NodeVisitor(node)
        vstr.apply(apply_fn, vstr, var_list, replace_blanks)

        """ Remove all the param nodes that we replaced earlier in the code. 
            This needs to be done in reverse order so that the locations of the parameter nodes, 
            which are saved in arrays, do not shift indexes. Otherwise you cannot reliably reference 
            the same nodes every time. God bless """
        for param_path in reversed(vstr.params_for_removal):
            for i, node in enumerate(vstr.nodes):
                vstr.nodes[i] = vstr.remove(vstr.nodes[i], param_path)
        to_return += vstr.nodes
    return to_return


def substitute_variables(nodes, var_list = {}, replace_blanks=False):
    """ This function finds and replaces all values found in the list of nodes passed into it. 
        Different from replace_variables which only does the replacement. Returns an array of 
        all the replaced trees using the values found in the nodes and present in the init var_list """
    
    if type(nodes) is not list: nodes = [nodes]
    for node in nodes:
        if type(node) is not bashlex.ast.node: raise ValueError('Error! bashparser.variables.substitute_variables(nodes != list of bashlex.ast.nodes)')
    if type(var_list) is not dict: raise ValueError('Error! bashparser.variables.substitute_variables(var_list != dict)')
    to_return = []

    for node in nodes:
        var_list = update_variable_list(node, var_list)
        to_return += replace_variables(node, var_list, replace_blanks)
    return to_return


def update_variable_list(nodes, var_list):
    """(node, variable dict) strips any variables out of ast and saves them to variable list. 
	returns an updated variable dict"""
    if type(nodes) is not list: nodes = [ nodes ]
    for node in nodes:
        if type(node) is not bashlex.ast.node: raise ValueError('Error! bashparser.variables.update_variable_list(node != list of bashlex.ast.node)')
    if type(var_list) is not dict: raise ValueError('Error! bashparser.variables.update_variable_list(var_list != dict)')

    def apply_fn(node, var_list):
        """ We need to treat a variable and for loop seperately because a string in a for loop is actually an array """
        if node.kind == 'assignment':
            name, value = node.word.split('=', maxsplit=1)
            var_list = add_variable_to_list(var_list, name, value, append=False)
        elif node.kind == 'for':
            var_list = update_var_list_with_for_loop(node, var_list)
        return CONT
    for node in nodes:
        NodeVisitor(node).apply(apply_fn, var_list)
    return var_list


def add_variable_to_list(var_list, name, values, append=True): 
    """ (variable dict, name, value) Adds the corresponding name and value to dictionary. If name exists in 
        the dictionary, the value is added. Prevents bugs with use of the var_list """

    if type(var_list) is not dict: raise ValueError('Error! bashparser.variables.add_variable_to_list(var_list != dict)')
    if type(name) is not str: raise ValueError('Error! bashparser.variables.add_variable_to_list(name != str)')
    if type(values) is not list: values = [ values ]
    
    """ We are only going to save things as arrays. This makes the unwrapping/replacing in the node structure easier """
    for i, val in enumerate(values):
        if type(val) is not str and type(val) is not bashlex.ast.node: values[i] = str(val)    

    if name in var_list and append:
        for val in values:
            if val not in var_list[name]:
                var_list[name] += [ val ]
    else: 
        var_list[name] = values
    return var_list


def update_var_list_with_for_loop(for_nodes, var_list, replace_blanks=False):
    """ This function takes a for_loop node and a variable list. It updated the value of the var_lits
        with the value that the for loop assigned to the iterator. This value could be a string, another variable, 
        or a command substitution. All cases are covered here. If another variable is specified, the value assigned 
        is a replication of the other variables value at that point in time, not a reference to the other variable """
    if type(for_nodes) is not list: for_nodes = [ for_nodes ]
    for for_node in for_nodes:
        if type(for_node) is not bashlex.ast.node: raise ValueError('Error! bashparser.variables.update_var_list_with_for_loop(node != bashlex.ast.node)')
    if type(var_list) is not dict: raise ValueError('Error! bashparser.variables.update_var_list_with_for_loop(var_list != dict)')
    
    for for_node in for_nodes:
        """ Verify the forloop has the format for X in Y. If not, then return the var_list unchanged. Could put error here but haven't had an issue yet """
        if not ( hasattr(for_node, 'parts') and len(for_node.parts) >= 3 and  
                hasattr(for_node.parts[0], 'word') and for_node.parts[0].word == 'for' and 
                hasattr(for_node.parts[2], 'word') and for_node.parts[2].word == 'in'  ) : return var_list 
        
        """ Gather all the info to be stripped from the for loop """
        name = for_node.parts[1].word
        value_index = 3
        variable_value = []
        value_nodes = []

        """ Strip the data from the for loop """
        while value_index < len(for_node.parts) and for_node.parts[value_index].word != ';' and for_node.parts[value_index].word !='do':
            """ Values can only be in word nodes so we check for variables, command siubsitutions, and any 
                nested options. We then convert it to its fully replaced form """
            if not len(for_node.parts[value_index].parts):
                variable_value += for_node.parts[value_index].word.split(' ')
            else:
                for part in for_node.parts[value_index].parts: 
                    if part.kind == 'parameter':
                        if part.value in var_list:
                            variable_value += var_list [ part.value ]
                        else:
                            pass    # The variable needs to have an empty value still
                    if part.kind == 'commandsubstitution':
                        value_nodes = substitute_variables(part, var_list, replace_blanks)
                        for value_node in value_nodes: 
                            variable_value += [ str(NodeVisitor(value_node)) ]
            value_index += 1

        """ Update the var_list with the new forloop iterator values """
        var_list = add_variable_to_list(var_list, name, variable_value)
    
    return var_list
