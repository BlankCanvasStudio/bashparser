#!/bin/python3
import bashlex, copy
from bashparser.ast import NodeVisitor
from bashparser.ast import CONT, DONT_DESCEND


cmd_creates_aliasing = { 'mv', 'cp' }


def build_alias_table(nodes, alias_table = {}):
    """ Takes a node, checks to see if its moving a file. If it is, you could be using cmd aliasing.
        These aliases get recorded in alias_table dict. In the event there is nested aliasing, the value
        in the alias table is the most nested value (if that makes sense). 
        Acts BY REFERENCE and returns for good measure. Can be used to expand already existing alias table """

    if type(nodes) is not list: nodes = [ nodes ]
    for node in nodes:
        if type(node) is not bashlex.ast.node: raise ValueError('Error! bashparser.build_alias_table(node != bashlex.ast.node)')
    if type(alias_table) is not dict: raise ValueError('Error! bashparser.build_alias_table(alias_table != dict)')

    def apply_fn(node, alias_table):
        if node.kind != 'command': return CONT

        # mv a b
        if len(node.parts) < 3: return CONT
        if node.parts[0].word not in cmd_creates_aliasing: return CONT 

        # Remove the cmd and any flags from the start of the parts array (NOT THE PARTS OF THE NODE)
        parts = node.parts[1:]
        while parts[0].word[0] == '-': parts = parts[1:]

        # find out what a is. If its another alias, replace it with the original value
        cmd_from = parts[0].word
        if cmd_from in alias_table: cmd_from = alias_table[cmd_from]

        # find out what b is
        cmd_to = parts[1].word

        # Add full path and file name to the alias table
        alias_table[cmd_to] = cmd_from
        if '/' in cmd_from: cmd_from = cmd_from.split('/')[-1]
        if '/' in cmd_to: cmd_to = cmd_to.split('/')[-1]
        alias_table[cmd_to] = cmd_from

        # Children of a command node are not further children. Only word & parameter nodes
        return DONT_DESCEND

    for node in nodes:
        NodeVisitor(node).apply(apply_fn, alias_table)
    return alias_table


def resolve_aliasing(nodes, alias_table = {}):
    """ This function replaces the command text of any command alias specified in the alias table 
        with the name of the function truly being executed. """
    
    if type(nodes) is not list: nodes = [ nodes ]
    for node in nodes:
        if type(node) is not bashlex.ast.node: raise ValueError('Error! bashparser.resolve_aliasing(node != bashlex.ast.node)')
    if type(alias_table) is not dict: raise ValueError('Error! bashparser.resolve_aliasing(alias_table != dict)')


    def cmd_alias_qual_fn(node, alias_table):
        # If its a command using the file, replace it
        if node.kind == 'command' and len(node.parts) and hasattr(node.parts[0], 'word') and node.parts[0].word in alias_table:
                return True 
        # If you are piping a repalced file change it
        elif node.kind == 'redirect':
            mem_nodes_to_unalias = ['input', 'output']
            for mem_node_name in mem_nodes_to_unalias:
                node_to_unalias = getattr(node, mem_node_name) 
                if node_to_unalias and hasattr(node_to_unalias, 'word') and node_to_unalias.word in alias_table:
                    return True 
        else: 
            return False 
    
    def cmd_alias_gen_fn(node_in, alias_table):
        """ Makes copy of aliased version of node,  resolves the aliasing, and returns the new adjusted node
            This acts BY VALUE not by reference """
        node = copy.deepcopy(node_in)
        # Replace the command text of the command node with the resolved alias
        if node.kind == 'command':  
            node.parts[0].word = alias_table[node.parts[0].word] 
        # Replace the section of the cmd which has been aliased in redirect
        elif node.kind == 'redirect':
            mem_nodes_to_unalias = ['input', 'output']      # Kinds of redirect node children which can contain aliasing
            for mem_node_name in mem_nodes_to_unalias:
                node_to_unalias = getattr(node, mem_node_name) 
                if node_to_unalias and hasattr(node_to_unalias, 'word') and node_to_unalias.word in alias_table:    # If that node contains aliasing, replace it
                    setattr(node_to_unalias, 'word', alias_table[node_to_unalias.word])
        return [ node ]
    
    to_return = []
    for node in nodes:
        to_return += NodeVisitor(node).replace(cmd_alias_qual_fn, {'alias_table':alias_table}, cmd_alias_gen_fn, {'alias_table':alias_table})
    return to_return


def build_and_resolve_aliasing(nodes, alias_table={}):
    """ A helpful wrapper so building and resolving can be done over a number of nodes at once 
        while still preserving internal order of aliasing """

    if type(nodes) is not list: nodes = [nodes]
    for node in nodes: 
        if type(node) is not bashlex.ast.node: raise ValueError('nodes must be a bashlex.ast.node')
    if type(alias_table) is not dict: raise ValueError('alias_table must be a dictionary')

    new_nodes = []
    for node in nodes:
        alias_table = build_alias_table(node, alias_table)
        new_nodes += resolve_aliasing(node, alias_table)

    return new_nodes
