#!/bin/python3
import bashparser, copy, bashlex
from bashparser.ast import NodeVisitor, CONT, DONT_DESCEND

class Chunk:
    def __init__(self, name, start, end):
        self.name = name 
        self.start = start
        self.end = end
    def __repr__(self):
        start = end = "None"
        if self.start: start = '[' + ','.join(str(x) for x in self.start) + ']'
        if self.end: end = '[' + ','.join(str(x) for x in self.end) + ']'
        return "Chunk(" + self.name + ', ' + start + ', ' + end + ')'
    def __str__(self):
        start = end = "None"
        if self.start: start = '[' + ','.join(str(x) for x in self.start) + ']'
        if self.end: end = '[' + ','.join(str(x) for x in self.end) + ']'
        return "Chunk(" + self.name + ', ' + start + ', ' + end + ')'
    

class ChunkConnection:
    def __init__(self, chunk, connected_to):
        self.chunk = chunk
        self.connected_to = connected_to
    def __repr__(self):
        return "ChunkConnection(chunk: " + str(self.chunk) +' connected to: ' + str(self.connected_to) + ')'
    def __str__(self):
        return "ChunkConnection(chunk: " + str(self.chunk) +' connected to: ' + str(self.connected_to) + ')'


def find_variable_chunks(nodes):
    if type(nodes) is not list: nodes = [nodes]

    def apply_fn(node, vstr, chunk_index, node_num):
        # full_path = [ node_num ] + vstr.path
        if node.kind == 'assignment':
            name = node.word.split('=', maxsplit=1)[0]
            if name not in chunk_index:
                new_chunk = Chunk(name, start=[node_num] + vstr.path, end=None)
                chunk_index[name] = [new_chunk]     # We use an array here cause there could be multiple chunks per variable
            else:
                chunk_index[name][-1].end = vstr.path
                new_chunk = Chunk(name, start=[node_num] + vstr.path, end=None)
                chunk_index[name] += new_chunk
        if node.kind == 'parameter':
            name = node.value
            if name in chunk_index:   # check to see if variable has been declared
                chunk_index[name][-1].end = [node_num] + vstr.path[:-1]   # This is going to update every time. Also path should be to word node not param node (imo)
                # A condition could be added here to iterate up the path until we hit a command node or an equivalent. But not useful quite yet
        return CONT

    chunk_index = {}
    for i, node in enumerate(nodes):
        vstr = NodeVisitor(node)
        vstr.apply(apply_fn, vstr, chunk_index, node_num = i)

    return [j for i in list(chunk_index.values()) for j in i]   # sweet sweet list comprehension


def find_cd_chunks(nodes):
    # This needs to be improved to take functions into account?
    if type(nodes) is not list: nodes = [nodes]
    chunks = []
    # Retieve all the cd commands
    commands = bashparser.return_paths_to_node_type(nodes, 'command')
    cds = []
    for command in commands: 
        if hasattr(command.node.parts[0], 'word') and command.node.parts[0].word == 'cd': cds += [ command ]
    # Build the chunks based off the cd commands found 
    i = 0
    while i < len(cds):
        chunk_start = cds[i].path
        
        # If the cds are right next to one another then we are going to increment the chunks cause chained cds should be in the same chunk
        test = True
        while test and i + 1 < len(cds):

            if len(cds[i].path) == 1 and len(cds[i+1].path) == 1 and cds[i].path[0] + 1 == cds[i+1].path[0]: i += 1
            elif len(cds[i].path) == 2 and len(cds[i+1].path) == 2 and cds[i].path[0] + 1 == cds[i+1].path[0]: i += 1
                # Idk if this ^^ Is really good or necessary when its unrolled
            elif cds[i].path[-1] == cds[i+1].path[-1] + 1 and cds[i].path[:-1] == cds[i+1].path[:-1]: i += 1
            else: test = False
            
        # Set the value of the end of the chunk
        if len(cds) > i + 1:  # If there is another cd between current location and EOF
            if cds[i+1].path[-1] > 0: chunk_end =  cds[i+1].path[:-1] +  [ cds[i+1].path[-1] - 1 ]
            else: chunk_end = cds[i+1].path[:-2] + [cds[i+1].path[-2] - 1] + [ 0 ]
        else:  # If there isn't a cd as the last line then set the final chunk to the nodes from last cd to end of file
            chunk_end = [ len(nodes) - 1 ]  # [ len(nodes) - 1, 0 ]  
        
        chunks += [Chunk('cd', chunk_start, chunk_end)]
        i += 1
    return chunks
        
        
def is_connected(chunk_one, chunk_two):
    if chunk_two.start[0] < chunk_one.start[0] and chunk_two.end[0]: return True 
    if chunk_two.start[0] < chunk_one.end[0] and chunk_two.end[0]: return True
    return False


def return_connected_chunks(chunks):
    variable_names = list(chunks.keys())
    # Check every key we have in dict
    connected_chunks = []
    for i, name in enumerate(variable_names):
        variable_chunks = chunks[name]
        # Check every chunk we have associated with a given key
        for chunk in variable_chunks:
            # Check that chunk vs all chunks associated with every following key (meaning its a 100% compared)
            for j_name in variable_names[i+1:]:
                for j_chunk in chunks[j_name]:
                    if is_connected(chunk, j_chunk):
                        connected_chunks += [ChunkConnection(chunk, j_chunk)]
    return connected_chunks


def var_is_used_in_declaration(assignment_node, var_name):
    variables = bashparser.return_nodes_of_type(assignment_node, 'parameter')
    for var in variables: 
        if var.value == var_name: return True
    return False


def return_dependent_chunks(connected_chunks, orig_nodes):
    # 4 dependencies: nested in same chunk, cd(?), used in the same line, used in definition, $2 acts on results of $1 command
    dependent_chunks = []
    for chunk in connected_chunks:
        # Used in variable definition
        assignments = bashparser.return_paths_to_node_type(orig_nodes, 'assignment')
        for assignment in assignments:
            if assignment.path > chunk.chunk.start: # This might break with the introduction of cd as first entry
                is_dependent = False
                if assignment.node.word.split('=')[0] == chunk.chunk.name: is_dependent = var_is_used_in_declaration(assignment.node, chunk.connected_to.name)
                if assignment.node.word.split('=')[0] == chunk.connected_to.name: is_dependent = var_is_used_in_declaration(assignment.node, chunk.chunk.name)
                if is_dependent:
                    dependent_chunks += [ chunk ]
                    break

    return dependent_chunks


def easy_nuclear_slicing(nodes):
    if type(node) is not list: nodes = [nodes]

    chunks = []

    for i in range(0, len(nodes)):
        for j in range(i+1, len(nodes)):
            chunks += [ Chunk(start=i, end=j) ]

    return chunks

# filename="testing.sh"

# nodes = bashparser.parse(open(filename).read())

# variable_assignments = bashparser.return_nodes_of_type(nodes, 'assignment')

# variable_uses = bashparser.return_variable_paths(nodes)

# variable_commands = return_variable_commands(nodes)

# chunks = find_variable_chunks(nodes)

# connected_chunks = return_connected_chunks(chunks)

# dependent_chunks = return_dependent_chunks(connected_chunks, nodes)

# print('dependent chunks: ')
# for chunk in dependent_chunks:
#     print(chunk)
