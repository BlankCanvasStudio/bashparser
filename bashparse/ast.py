# from bashparse.path_variable import path_variable
import bashlex, copy

CONT = 0
DONT_DESCEND = 1

class NodeVisitor:
    def __init__(self, root):
        self._path = []
        self._root = root
        self._string = ''
        self._nodes = [ root ]
        self._accum_deltas = [ 0 ]
        self._replaced_variables = {}
        self._variable_replacement_order = []
        self._replaced_functions = {}
        self.no_children = {'operator', 'reservedword', 'pipe', 'parameter', 'tilde', 'heredoc'}
        self.parts_children = {'list', 'pipeline', 'if', 'for', 'while', 'until', 'command', 'function', 'word', 'assignment'}
        self.command_children = {'commandsubstitution', 'processsubstitution'}
        self.passable_nodes = {'command', 'list', 'compound', 'for', 'parameter', 'function'}
        self.list_children = {}
        self.contains_variable_text = {'word', 'assignment'}

    def __str__(self):
        self._string = ""
        
        def apply_fn(node):
            k = node.kind
            word = ''
            if node.kind == 'operator': word = node.op
            elif node.kind == 'commandsubstitution': 
                word = '$('
                cmd = node.command
                for part in cmd.parts:
                    word += str(NodeVisitor(part)) + ' '
                word = word[:-1] + ')'
                self._string = self._string + word + ' '
                
                return DONT_DESCEND

            elif hasattr(node, 'word'): word = node.word 
            elif node.kind in self.passable_nodes: return CONT
            else: 
                raise ValueError('unsupported node kind encountered in convert_tree_to_string: ', node.kind)
            self._string = self._string + word + ' '
            return CONT
        self.apply(apply_fn)
        return self._string[:-1]     # remove trailing space cause wrong

    def __type__(self):
        return 'bashparse.ast.NodeVisitor'      # No shot this is the proper implementation but it'll do

    @property
    def path(self):
        return self._path
    @path.setter
    def path(self, path):
        self._path = path

    @property
    def root(self):
        return self._root

    @property
    def nodes(self):
        return self._nodes
    @nodes.setter
    def nodes(self, nodes):
        if type(nodes) is not list: nodes = [nodes]
        self._nodes = nodes
    
    @property
    def variable_replacement_order(self):
        return self._variable_replacement_order
    @variable_replacement_order.setter
    def variable_replacement_order(self, new_order):
        if type(new_order) is not list: raise ValueError("Error! NodeVisitor.variable_replacement_order must be a list")
        self._variable_replacement_order = new_order

    @property
    def replaced_variables(self):
        return self._replaced_variables
    @replaced_variables.setter
    def replaced_variables(self, replaced_variables):   # Do we even need this cause dict?
        if type(replaced_variables) is not dict: raise ValueError("Error! NodeVisitor.replaced_variables must be a dict")
        self._replaced_variables = replaced_variables
    
    @property
    def replaced_functions(self):
        return self.replaced_functions
    @replaced_functions.setter
    def replaced_functions(self, replaced_functions):   # Do we even need this cause set?
        if type(replaced_functions) is not set: return ValueError("Error! NodeVisitor.replaced_functions must be a set")
        self.replaced_functions = replaced_functions

    @property
    def accum_deltas(self):
        return self._accum_deltas
    @accum_deltas.setter 
    def accum_deltas(self, new_array):
        self._accum_deltas = new_array

    @property
    def parent(self):
        if not len(self._path): return None
        else: return self.at_path(self._root, self._path[:-1])


    def apply(self, apply_fn, *args, **kwargs):
        # We split it this way so path is reset every time 
        # There is probably a more elegant solution that I will switch to later
        
        def run(node, *args, **kwargs):
            rt_val = apply_fn(node, *args, **kwargs)
            if rt_val == DONT_DESCEND: return                      
            current_path = self._path
            for i, child in enumerate(self.children(node)):
                self._path = current_path + [ i ]
                rt_val = run(child, *args, **kwargs)
            return rt_val
        self._path = []   
        run(self._root, *args, **kwargs)
        return self      

    def children(self, node = None):
        """ Returns all the children of the root node """
        # Should we return none or an empty array (going with empty array for beaty in apply code)
        # Should we allow this to take arguments rather than be bound to a specific ast?
        if node is None: node = self._root
        k = node.kind

        if k in self.parts_children:
            return node.parts
        elif k in self.no_children:
            return []
        elif k in self.command_children:
            return [ node.command ]
        elif k == 'compound':
            if hasattr(node, 'list'):
                return node.list
            elif hasattr(node,'redirects'):
                return [ node.redirects ]
        elif k == 'redirect':
            if isinstance(node.output, bashlex.ast.node):
                return [ node.output ]
            if node.heredoc:
                return [ node.heredoc[child_num] ]
        elif hasattr(node, 'list'):
            return node.list
        else:
            raise ValueError('unknown node kind %r' % k)

    def child(self, node = None, num = 0):
        """ Returns the child with number specified by argument 
            ie can return the 3rd child of the root node (helpful for paths) """
        # Could add error conditions here
        if node is None: node = self._root
        children = self.children(node)
        try:
            return children[num]
        except Exception as e:
            print('\nError in indexing children of node for child')
            print('root:', node)
            print('children:', children)
            print('num: ', num)
            print('len: ', len(children))
            print('\n\n')

    def set_children(self, parent, children):
        if type(children) is not list: raise ValueError("NodeVisitor.children must be set to array of bashlex.ast.nodes")
        for tmp_n in children: 
            if type(tmp_n) is not bashlex.ast.node: raise ValueError("NodeVisitor.children must be set to array of bashlex.ast.nodes")
        
        k = parent.kind

        if k in self.parts_children:
            parent.parts = children
        elif len(children) and k in self.no_children:
            raise ValueError("Error! Node assigned children but necessarily has none")
        elif k in self.command_children:
            if len(children) != 1: raise ValueError("Error! Assigned multiple values to a Node's command attr")
            parent.command = children[0]
        elif k == 'compound':
            if hasattr(parent, 'list'):
                parent.list = children
            elif hasattr(parent,'redirects'):
                if len(children) != 1: raise ValueError("Error! Assigned multiple values to a Node's redirects attr")
                parent.redirects = children[0]
        elif k == 'redirect':
            if isinstance(parent.output, bashlex.ast.node):
                if len(children) != 1: raise ValueError("Error! Assigned multiple values to a Node's output attr")
                parent.output = children[0]
            if parent.heredoc:
                parent.heredoc = children
        elif hasattr(parent, 'list'):
            parent.list = children
        else:
            raise ValueError('unknown node kind %r' % k)
        return parent

    def remove(self, root = None, path = None):
        if root is None: root = self._root 
        if path is None: path = self._path
        # root = copy.deepcopy(root)    # I think the root should be mutable in this way. Maybe its bad and I'm wrong
        parent = root
        for i in path[:-1]: parent = self.child(parent, i)
        p_vstr = NodeVisitor(parent)
        new_children = p_vstr.children()[:path[-1]] + p_vstr.children()[path[-1]+1:]
        p_vstr.set_children(parent, new_children)
        return root

    def at_path(self, node = None, path = None):
        # Should we use the interal path variable for this?
        if node is None: node = self._root
        if path is None: path = self._path
        current_node = node
        for el in path: 
            current_node = self.child(current_node, el)
        return current_node

    def replace_node(self, root, path, new_child):
        node = copy.deepcopy(root)
        parent = self.at_path(node, path[:-1])

        if not len(path): return new_child

        try:
            old_child = self.child(parent, path[-1])
        except: 
            print()
            print('parent:\n'+ parent.dump())
            print('path:\n', path)
            print('new child:\n', new_child.dump())
            print()
            raise ValueError('index into children is not valid')
        
        if new_child.pos[0] != old_child.pos[0]:
            new_child = justify(new_child)
            new_child = align(new_child, old_child.pos[0])

        k = parent.kind
        num_child_nodes = 0

        if len(path) == 0:      
            return new_child
        elif k in self.parts_children:

            if len(parent.parts) >= path[-1]: 
                parent.parts[path[-1]] = new_child
        elif k in self.no_children:
            raise ValueError('Error! You are trying to replace the child of a node which, by definition, has no children. Function: bashparse.ast.NodeVisitor.replace')
        elif k in self.command_children:
            num_child_nodes = len(parent.command) 
            if num_child_nodes >= path[-1]:
                parent.command[path[-1]] = new_child
        elif k == 'compound':
            if hasattr(node, 'list'):
                num_child_nodes = len(parent.list)
                if num_child_nodes >= path[-1]: 
                    parent.list[path[-1]] = new_child
            elif hasattr(parent,'redirects'):
                child_nodes += 1
                if path[-1] == 0:
                    parent.redirect = new_child
        elif k == 'redirect':
            if isinstance(node.output, bashlex.ast.node):
                num_child_nodes += 1
                parent.output = new_child
            if parent.heredoc:
                num_child_nodes = len(parent.heredoc[path[-1]])
                if num_child_nodes >= path[-1]: 
                    parent.heredoc[path[-1]] = new_child
        else:
            raise ValueError('unknown node kind %r' % k)
        
        if self.child(parent, path[-1]) != new_child:
            raise ValueError('Error! bashparse.ast.NodeVisitor.replace did not change the node properly')

        return node

    def replace(self, qual_fn, qual_fn_args, gen_fn, gen_fn_args):
        def apply_fn(node, self, qualification_fn, qualification_args, generation_fn, generation_fn_args):
            if qualification_fn(node, **qualification_args):
                replacement_nodes = generation_fn(node, **generation_fn_args)
                new_nodes = []
                for replacement_node in replacement_nodes:
                    for self_node in self._nodes:
                        new_node = copy.deepcopy(self_node)
                        tmp = self.replace_node(new_node, copy.deepcopy(self._path), replacement_node)

                        new_nodes += [ tmp ]
                self._nodes = new_nodes
                return DONT_DESCEND
            else:
                return CONT

        self.apply(apply_fn, self, qual_fn, qual_fn_args, gen_fn, gen_fn_args)
        return self._nodes


def align(node, delta):
    def adjust_pos(node, delta):
        start = (node.pos[0] + delta) if ((node.pos[0] + delta) > 0) else 0
        node.pos = ( start, node.pos[1] + delta )
        return CONT
    
    return NodeVisitor(root=node).apply(adjust_pos, delta).root

def justify(node):
    return align(node, -node.pos[0])

def expand_ast_along_path(root, path_to_update, delta):
    if type(root) is not bashlex.ast.node: raise ValueError('node must be a bashparse.node')
    if type(path_to_update) is not list: raise ValueError('path_to_update must be a list')
    if type(delta) is not int: raise ValueError('delta must be an int')
    node = copy.deepcopy(root)
    node_root = node
    vstr = NodeVisitor(node)
    node.pos = (node.pos[0], node.pos[1] + delta)
    for i in path_to_update:
        node = vstr.child(node, i)
        node.pos = (node.pos[0], node.pos[1] + delta)
    return node_root


    def apply_fn(node, vstr, path_to_update, delta):
        length = len(path_to_update) if len(path_to_update) < len(vstr.path) else len(vstr.path)
        for i in range(0, length):
            if path_to_update[i] != vstr.path[i]: return DONT_DESCEND
        
        node.pos = (node.pos[0], node.pos[1] + delta)
        return CONT

    vstr = NodeVisitor(node)
    vstr.apply(apply_fn, vstr, path_to_update, delta)
    return vstr.root

def shift_ast_right_of_path(node, path_to_update, delta):
    
    if type(node) is not bashlex.ast.node: raise ValueError('node must be a bashparse.node')
    if type(path_to_update) is not list: raise ValueError('path_to_update must be a list')
    if type(delta) is not int: raise ValueError('delta must be an int')

    def apply_fn(node, vstr, path_to_update, delta):
        length = len(path_to_update) if len(path_to_update) < len(vstr.path) else len(vstr.path)
        greater = False
        for i in range(0, length):
            if path_to_update[i] > vstr.path[i] and not greater: return CONT
            if path_to_update[i] < vstr.path[i]: greater = True
        if not greater: return CONT
        new_start = node.pos[0] + delta if \
                        ((node.pos[0] + delta > 0) and (node.pos[0] != 0)) else 0
        new_end = node.pos[1] + delta
        node.pos = (new_start, new_end)
        return CONT

    vstr = NodeVisitor(node)
    vstr.apply(apply_fn, vstr, path_to_update, delta)
    return vstr.root
