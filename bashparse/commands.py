import bashlex, copy
from bashparse.ast import NodeVisitor
from bashparse.ast import CONT

def return_command_aliasing(nodes, command_alias_list = {}):
    if type(nodes) is not list: nodes = [nodes]
    for node in nodes: 
        if type(node) is not bashlex.ast.node: raise ValueError('nodes must be a bashlex.ast.node')
    if type(command_alias_list) is not dict: raise ValueError('command_alias_list must be a dictionary')
    
    class CommandAliasLocator(NodeVisitor):
        def __init__(self, node, command_alias_list):
            super(CommandAliasLocator, self).__init__(root=node)
            self.command_alias_list = command_alias_list
        def apply(self):
            NodeVisitor.apply(self, self.apply_fn)
        def apply_fn(self, node):
            if node.kind != 'command': return
            if not (len(node.parts) > 2 and (node.parts[0].word == 'mv' or node.parts[0].word == 'cp' )): return
            
            non_flag_base = 1
            while non_flag_base + 1 < len(node.parts) and node.parts[non_flag_base].word[0] == '-':
                non_flag_base += 1
            original_name = node.parts[non_flag_base].word
            new_name = node.parts[non_flag_base + 1].word
            if original_name in command_alias_list:
                original_name = command_alias_list[original_name]
            command_alias_list[new_name] = original_name
            if '/' in original_name: original_name = original_name.split('/')[-1]
            if '/' in new_name: new_name = new_name.split('/')[-1]
            command_alias_list[new_name] = original_name

    for node in nodes:
        CommandAliasLocator(node, command_alias_list).apply()

    return command_alias_list

def replace_command_aliasing(node, command_alias_list = {}):
    def cmd_alias_qual_fn(node, command_alias_list):
        if node.kind == 'command' and hasattr(node, 'parts') and len(node.parts) and hasattr(node.parts[0], 'word') and node.parts[0].word in command_alias_list:
            return True 
        elif node.kind == 'redirect':
            mem_nodes_to_unalias = ['input', 'output']
            for mem_node_name in mem_nodes_to_unalias:
                node_to_unalias = getattr(node, mem_node_name) 
                if node_to_unalias and hasattr(node_to_unalias, 'word') and node_to_unalias.word in command_alias_list:
                    return True 
        else: 
            return False 
    
    def cmd_alias_gen_fn(root, command_alias_list):
        node = copy.deepcopy(root)
        if node.kind == 'command':
            node.parts[0].word = command_alias_list[node.parts[0].word] 
        elif node.kind == 'redirect':
            mem_nodes_to_unalias = ['input', 'output']
            for mem_node_name in mem_nodes_to_unalias:
                node_to_unalias = getattr(node, mem_node_name) 
                if node_to_unalias and hasattr(node_to_unalias, 'word') and node_to_unalias.word in command_alias_list:
                    setattr(node_to_unalias, 'word', command_alias_list[node_to_unalias.word])
        return [ node ]
    return NodeVisitor(node).replace(cmd_alias_qual_fn, {'command_alias_list':command_alias_list}, cmd_alias_gen_fn, {'command_alias_list':command_alias_list})
    


def resolve_command_aliasing(nodes, command_alias_list={}):
    if type(nodes) is not list: nodes = [nodes]
    for node in nodes: 
        if type(node) is not bashlex.ast.node: raise ValueError('nodes must be a bashlex.ast.node')
    if type(command_alias_list) is not dict: raise ValueError('command_alias_list must be a dictionary')

    new_nodes = []
    for node in nodes:
        command_alias_list = return_command_aliasing(node, command_alias_list)
        new_nodes += replace_command_aliasing(node, command_alias_list)

    return new_nodes
