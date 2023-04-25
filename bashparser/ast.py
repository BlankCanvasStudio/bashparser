#!/bin/python3
import bashlex, copy, bashparser
from ordered_set import OrderedSet


CONT = 0
DONT_DESCEND = 1
HALT = 2


class NodeVisitor:
    def __init__(self, root):
        self._path = []
        self._root = root
        self._string = ''
        self._nodes = [ copy.deepcopy(root) ]
        self._accum_deltas = [ 0 ]
        self._variable_replacement_order = OrderedSet()
        self._params_for_removal = []
        self.no_children = {'operator', 'reservedword', 'pipe', 'parameter', 'tilde', 'heredoc'}
        self.parts_children = {'list', 'pipeline', 'if', 'for', 'while', 'until', 'command', 'function', 'word', 'assignment'}
        self.command_children = {'commandsubstitution', 'processsubstitution'}
        self.passable_nodes = {'command', 'list', 'for', 'parameter', 'function', 'pipeline', 'if', 'while'}
        self.list_children = {}
        self.contains_variable_text = {'word', 'assignment'}


    def __str__(self):
        """ Don't let it save itself, always recompute. Much easier than changing every time """
        if self.root is None:
            return ''

        self._string = ""
        
        def apply_fn(node):
            k = node.kind
            word = ''
            if node.kind in self.passable_nodes: return CONT
            elif node.kind == 'operator': word = node.op
            elif node.kind == 'pipe': word = node.pipe
            elif node.kind == 'redirect': 
                if type(node.input) == bashlex.ast.node:
                    word += str(NodeVisitor(node.input))
                elif node.input is not None: 
                    word += str(node.input)
                word += str(node.type)
                if type(node.output) == bashlex.ast.node:
                    word += str(NodeVisitor(node.output))
                elif node.output is not None:
                    word += str(node.output)
                self._string = self._string + ' ' + word
                return DONT_DESCEND
            elif node.kind == 'compound':
                for part in node.list:
                    word += ' ' + str(NodeVisitor(part))
                if hasattr(node, 'redirects'):
                    for part in node.redirects:
                        word += ' ' + str(NodeVisitor(part))
                self._string = self._string + ' ' + word
                return DONT_DESCEND
            elif node.kind == 'commandsubstitution': 
                word = '$('
                cmd = node.command
                for part in cmd.parts:
                    word += str(NodeVisitor(part)) + ' '
                word = word[:-1] + ')'
                self._string = self._string + ' ' + word
                return DONT_DESCEND

            elif hasattr(node, 'word'): 
                word = node.word
                self._string = self._string + ' ' + word
                return DONT_DESCEND 
            else: 
                raise ValueError('Error! Unsupported node kind encountered when converting NodeVisitor to string: ', node.kind)
            self._string = self._string + ' ' + word
            return CONT

        self.apply(apply_fn)
        return self._string.strip() # remove surrounding spaces cause wrong


    def __type__(self):
        return 'bashparser.ast.NodeVisitor'      # Praying this is the proper implementation


    """ Used for any indexing purposes when divergent asts are involved and modified when no divergence ops are specified"""
    @property
    def root(self):
        return self._root


    """ A list of all divergent asts when doing things like variable replacement  """
    @property
    def nodes(self):
        return self._nodes
    @nodes.setter
    def nodes(self, nodes):
        if type(nodes) is not list: nodes = [nodes]
        for node in nodes: 
            if type(node) is not bashlex.ast.node: raise ValueError("Error! Attribute NodeVisitor.nodes can only be set to an array of bashlex.ast.nodes")
        self._nodes = nodes


    """ Can be used with apply to locate your position in the ast at any given time """
    @property
    def path(self):
        return self._path
    @path.setter
    def path(self, path):
        if type(path) is not list: path = [ path ]
        for el in path: 
            if type(el) is not int: raise ValueError('Error! Attribute NodeVisitor.path can only be set to an array of ints')
        self._path = path


    """ Used When replacing variables. Needed to break self.nodes into slices of replacement chunks """
    @property
    def variable_replacement_order(self):
        return self._variable_replacement_order
    @variable_replacement_order.setter
    def variable_replacement_order(self, new_order):
        if type(new_order) is not list: raise ValueError("Error! NodeVisitor.variable_replacement_order must be a list")
        self._variable_replacement_order = new_order


    """ Parameter nodes need to be removed in reverse order to traversal order is the same. 
        But traversal needs to happen in the forward direction. We use this in replace_variables to 
        keep track of everywhere we need to remove a parameter """
    @property
    def params_for_removal(self):
        return self._params_for_removal
    @params_for_removal.setter
    def params_for_removal(self, params_for_removal):   # Do we even need this cause dict?
        if type(params_for_removal) is not list: raise ValueError("Error! NodeVisitor.params_for_removal must be a dict")
        self._params_for_removal = params_for_removal


    """ accumulated_deltas. When dealing with multiple trees in self.nodes, tracking shifts in the ast gets annoying so we do it all at once.
        This property is used to allow for inline variable replacement without needing to revist nodes for alignment over an arbitrary number of trees """
    @property
    def accum_deltas(self):
        return self._accum_deltas
    @accum_deltas.setter 
    def accum_deltas(self, new_array):
        if type(new_array) is not list: raise ValueError("Error! NodeVisitor.accum_deltas can only be set to a list.")
        self._accum_deltas = new_array


    """ A useful but dangerous property. In apply() it can be used to return the current parent if the NodeVisitor is passed into the function. """
    @property
    def parent(self):
        if not len(self._path): return None
        else: return self.at_path(self._root, self._path[:-1])



    def apply(self, apply_fn, *args, **kwargs):
        """ This function tries to run apply_fn(*args, **kwargs) on every node in the ast using a depth first search (L to R). 
            By returning CONT, DONT_DESCEND, or HALT from apply_fn you can affect the traversal through the ast. 
            Return value effects:
                DONT_DESCEND - None of the current node's children will be searched
                CONT - Continue searching the tree
                HALT - Exit search 
        """

        def run(node, *args, **kwargs):
            rt_val = apply_fn(node, *args, **kwargs)
            if rt_val == DONT_DESCEND: return CONT       
            if rt_val == HALT: return HALT              
            current_path = self._path
            for i, child in enumerate(self.children(node)):
                self._path = current_path + [ i ]
                rt_val = run(child, *args, **kwargs)
                if rt_val == HALT: return HALT
            return rt_val
        self._path = []   
        run(self._root, *args, **kwargs)
        return self      


    def apply_along_path(self, apply_fn, path, *args, **kwargs):
        """ Applies a function along a path. Acts just like apply but on a path """
        current_node = self._root
        rt_val = apply_fn(current_node, *args, **kwargs)
        if rt_val == HALT or rt_val == DONT_DESCEND: return self
        for i in path:
            current_node = self.child(current_node, i)
            rt_val = apply_fn(current_node, *args, **kwargs)
            if rt_val == HALT or rt_val == DONT_DESCEND: return self
        return self


    def apply_right_of_path(self, apply_fn, path, *args, **kwargs):
        """ Like apply but it only acts on the right side of the path specified. Exclusive of the path itself """
        if type(path) is not list: raise ValueError('path_to_update must be a list')

        def apply_right_fn(node, apply_fn, path, vstr, *args, **kwargs):
            length = len(path) if len(path) < len(vstr.path) else len(vstr.path)
            greater = False
            for i in range(0, length):
                if path[i] > vstr.path[i] and not greater: return CONT
                if path[i] < vstr.path[i]: greater = True
            if not greater: return CONT
            return apply_fn(node, *args, **kwargs)

        return self.apply(apply_right_fn, apply_fn, path, self, *args, **kwargs)


    def apply_left_of_path(self, apply_fn, path, *args, **kwargs):
        """ Like apply but it only acts on the left side of the path specified. Exclusive of the path itself """
        if type(path) is not list: raise ValueError('path_to_update must be a list')

        def apply_right_fn(node, apply_fn, path, vstr, *args, **kwargs):
            length = len(path) if len(path) < len(vstr.path) else len(vstr.path)
            lesser = False
            for i in range(0, length):
                if path[i] < vstr.path[i] and not lesser: return CONT
                if path[i] > vstr.path[i]: lesser = True
            if not lesser: return CONT
            return apply_fn(node, *args, **kwargs)

        return self.apply(apply_right_fn, apply_fn, path, self, *args, **kwargs)


    def at_path(self, root = None, path = None):
        """ Returns BY REFERENCE the node a path specified from the root passed in """
        if root is None: root = self._root
        if path is None: path = self._path
        if type(root) is not bashlex.ast.node: raise ValueError("Error! Invalid type. NodeVisitor.at_path(root != bashlex.ast.node)")
        if type(path) is not list: raise ValueError("Error! Invalid type. NodeVisitor.at_path(path != list)")
        for el in path: root = self.child(root, el)
        return root


    def children(self, root = None):
        """ Returns an array of all the children of either the root passed in or the root node of NodeVisitor if none specified. 
            If there are no children, an empty array is returned"""

        if root is None: root = self._root
        k = root.kind

        if k in self.parts_children:
            return root.parts
        elif k in self.no_children:
            return []
        elif k in self.command_children:
            return [ root.command ]
        elif k == 'compound':
            if hasattr(root, 'list'):
                return root.list
            elif hasattr(root,'redirects'):
                return [ root.redirects ]
        elif k == 'redirect':
            if isinstance(root.output, bashlex.ast.node):
                return [ root.output ]
            elif root.heredoc:
                return [ root.heredoc[child_num] ]
            else:
                return []
        elif hasattr(root, 'list'):
            return root.list
        else:
            raise ValueError('unknown node kind %r' % k)


    def child(self, root = None, num = 0):
        """ Returns the child with number specified by argument 
            (ie can return the 3rd child of the root node (helpful for path finding) """
        # Could add error conditions here
        if root is None: root = self._root
        children = self.children(root)
        try:
            return children[num]
        except Exception as e:
            raise ValueError('Error! NodeVisitor.child #'+str(num)+' does not exist!')


    def set_children(self, root=None, children=[]):
        """ Takes a root bashlex.ast.node and an array of bashlex.ast.node children.
            Returns the new node & children combo. Technically, BY REFERENCE not copy """
        if root is None: root = self._root
        if type(children) is not list: children = [ children ]
        for tmp_n in children: 
            if type(tmp_n) is not bashlex.ast.node: raise ValueError("NodeVisitor.children must be set to array of bashlex.ast.nodes")
        
        k = root.kind

        if k in self.parts_children:
            root.parts = children
        elif len(children) and k in self.no_children:
            raise ValueError("Error! Node assigned children but necessarily has none")
        elif k in self.command_children:
            if len(children) != 1: raise ValueError("Error! Assigned multiple values to a Node's command attr")
            root.command = children[0]
        elif k == 'compound':
            if hasattr(root, 'list'):
                root.list = children
            elif hasattr(root,'redirects'):
                if len(children) != 1: raise ValueError("Error! Assigned multiple values to a Node's redirects attr")
                root.redirects = children[0]
        elif k == 'redirect':
            if isinstance(root.output, bashlex.ast.node):
                if len(children) != 1: raise ValueError("Error! Assigned multiple values to a Node's output attr")
                root.output = children[0]
            if root.heredoc:
                root.heredoc = children
        elif hasattr(root, 'list'):
            root.list = children
        else:
            raise ValueError('unknown node kind %r' % k)
        return root


    def swap_node(self, child, root = None, path = None):
        """ This replaces the node at the path specified with the child passed in
            both of these actions are BY REFERENCE """
        if root is None: root = self.root
        if path is None: path = self.path()

        parent = self.at_path(root, path[:-1])

        if not len(path): return child

        try:
            old_child = self.child(parent, path[-1])
        except: 
            raise ValueError('index into children is not valid')


        """ Move the ast to account for the new node & adjst the new node """
        self.justify(child)
        self.align(child, old_child.pos[0])
        delta = child.pos[1] - old_child.pos[1]
        bashparser.ast.expand_ast_along_path(root, path[:-1], delta)
        bashparser.ast.shift_ast_right_of_path(root, path, delta)

        k = parent.kind
        num_child_nodes = 0

        """ Actually inject the new child """
        if len(path) == 0:      
            return child
        elif k in self.parts_children:
            if len(parent.parts) >= path[-1]: 
                parent.parts[path[-1]] = child
        elif k in self.no_children:
            raise ValueError('Error! You are trying to replace the child of a node which, by definition, has no children. Function: bashparser.ast.NodeVisitor.replace')
        elif k in self.command_children:
            num_child_nodes = len(parent.command) 
            if num_child_nodes >= path[-1]:
                parent.command[path[-1]] = child
        elif k == 'compound':
            if hasattr(root, 'list'):
                num_child_nodes = len(parent.list)
                if num_child_nodes >= path[-1]: 
                    parent.list[path[-1]] = child
            elif hasattr(parent,'redirects'):
                child_nodes += 1
                if path[-1] == 0:
                    parent.redirect = child
        elif k == 'redirect':
            if isinstance(root.output, bashlex.ast.node):
                num_child_nodes += 1
                parent.output = child
            if parent.heredoc:
                num_child_nodes = len(parent.heredoc[path[-1]])
                if num_child_nodes >= path[-1]: 
                    parent.heredoc[path[-1]] = child
        else:
            raise ValueError('unknown node kind %r' % k)
        
        """ Error checking for sanity sake """
        if self.child(parent, path[-1]) != child:
            raise ValueError('Error! bashparser.ast.NodeVisitor.replace did not change the node properly')

        return root


    def replace(self, qual_fn, qual_fn_args, gen_fn, gen_fn_args):
        """ This function is going to sound really weird but its more useful than you think
        You can pass in a "qualifying function" and its arguments as a dictionary. This function needs to take a node as 
        its first argument. It needs to return true wherever in the ast you'd like to replace a node and false everywhere else. 
        You can pass the node visitor calling .replace() into the qualification function to get information & tooling. 
        Then when it returns positive, the generator function is run. The generator function must also take a node as its first arg. 
        The generator function needs to return an array of nodes that you would like to replace the current node with.
        This function then replaces all nodes specified by the qualifying function with the nodes generated and returns these nodes 
        as an array. """
        
        def apply_fn(node, self, qualification_fn, qualification_args, generation_fn, generation_fn_args):
            if qualification_fn(node, **qualification_args):
                replacement_nodes = generation_fn(node, **generation_fn_args)
                new_nodes = []
                for replacement_node in replacement_nodes:
                    for self_node in self._nodes:
                        new_node = copy.deepcopy(self_node)
                        tmp = self.swap_node(root=new_node, path=copy.deepcopy(self._path), child=replacement_node)

                        new_nodes += [ tmp ]
                self._nodes = new_nodes
                return DONT_DESCEND
            else:
                return CONT

        self.apply(apply_fn, self, qual_fn, qual_fn_args, gen_fn, gen_fn_args)
        return self._nodes


    def remove(self, root=None, path=None, child=None):
        """ Removes the node at path specified from root's tree. Passed in by reference 
            and returned for good measure. If a child is specified, then the path is actually to the 
            parent. The child which matches the child passed in is then removed. """
        if root is None: root = self._root
        if type(root) is not bashlex.ast.node: raise ValueError("Error! NodeVisitor.remove(root != bashlex.ast.node)")
        if type(path) is not list: raise ValueError("Error! NodeVisitor.remove(path != list)")
        parent = root
        for i in path[:-1]: parent = self.child(parent, i)
        if child is None:
            p_vstr = NodeVisitor(parent)
            new_children = p_vstr.children()[:path[-1]] + p_vstr.children()[path[-1]+1:]
            p_vstr.set_children(parent, new_children)
        else: 
            if type(child) is not bashlex.ast.node: raise ValueError("Error! NodeVisitor.remove(child != bashlex.ast.node)")
            parent = self.child(parent, path[-1])
            for i, current_child in enumerate(self.children(parent)): 
                if current_child == child: 
                    root = self.remove(parent, [i]) 
                    break
        return root


    def align(self, root = None, delta = None):
        """ This function shifts the pos attr of all nodes in self._root or node passed in by delta
            BY REFERENCE and returns the node for good measure """
        if root is None: root = self._root
        if type(root) is not bashlex.ast.node: raise ValueError("Error! NodeVisitor.align(root != bashlex.ast.node)")
        if type(delta) is not int: raise ValueError("Error! NodeVisitor.align(delta != int)")
        def adjust_pos(root, delta):
            start = (root.pos[0] + delta) if ((root.pos[0] + delta) > 0) else 0
            root.pos = ( start, root.pos[1] + delta )
            return CONT
        NodeVisitor(root=root).apply(adjust_pos, delta)    
        return root


    def justify(self, root = None):
        """ This function shifts the ast so it starts at zero. Basic wrapper around align. """
        if root is None: root = self._root
        if type(root) is not bashlex.ast.node: raise ValueError("Error! NodeVisitor.justify(root != bashlex.ast.node)")
        return NodeVisitor(root).align(delta = -root.pos[0])



def expand_ast_along_path(root, path_to_update, delta):
    """ This function expands the pos attribute to the right along a path by amount delta. Useful for variable replacement & updating.
        Updates the value BY REFERENCE """
    if type(root) is not bashlex.ast.node: raise ValueError('Error! bashparser.ast.expand_ast_along_path(node != bashparser.node)')
    if type(path_to_update) is not list: raise ValueError('Error! bashparser.ast.expand_ast_along_path(path != list)')
    if type(delta) is not int: raise ValueError('delta must be an int')
    def apply_fn(node, delta): node.pos = (node.pos[0], node.pos[1] + delta)
    return NodeVisitor(root).apply_along_path(apply_fn, path_to_update, delta).root


def shift_ast_right_of_path(root, path_to_update, delta):
    """ Takes a root and adds the delta to both pos attributes if its to the right of the path. Excludes the path.
        Functions BY REFERENCE not value but returns the root for posterity sake """
    if type(root) is not bashlex.ast.node: raise ValueError('root must be a bashparser.node')
    if type(path_to_update) is not list: raise ValueError('path_to_update must be a list')
    if type(delta) is not int: raise ValueError('delta must be an int')

    def apply_fn(node, delta):
        new_start = node.pos[0] + delta if ((node.pos[0] + delta > 0) and (node.pos[0] != 0)) else 0
        new_end = node.pos[1] + delta
        node.pos = (new_start, new_end)
    return NodeVisitor(root).apply_right_of_path(apply_fn, path_to_update, delta).root
