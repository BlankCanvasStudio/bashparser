# from bashparse.path_variable import path_variable
import bashlex, copy

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
        """ Don't let it save itself, always recompute. Much easier than changing every time """
        self._string = ""
        
        def apply_fn(node):
            k = node.kind
            word = ''
            if node.kind in self.passable_nodes: return CONT
            elif node.kind == 'operator': word = node.op
            elif node.kind == 'commandsubstitution': 
                word = '$('
                cmd = node.command
                for part in cmd.parts:
                    word += str(NodeVisitor(part)) + ' '
                word = word[:-1] + ')'
                self._string = self._string + word + ' '
                
                return DONT_DESCEND

            elif hasattr(node, 'word'): word = node.word 
            else: 
                raise ValueError('Error! Unsupported node kind encountered when converting NodeVisitor to string: ', node.kind)
            self._string = self._string + word + ' '
            return CONT

        self.apply(apply_fn)
        return self._string[:-1]     # remove trailing space cause wrong


    def __type__(self):
        return 'bashparse.ast.NodeVisitor'      # Praying this is the proper implementation


    """ Can be used with apply to locate your position in the ast at any given time """
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
        for node in nodes: 
            if type(node) is not bashlex.ast.node: raise ValueError("Error! Attribute NodeVisitor.nodes can only be set to an array of bashlex.ast.nodes")
        self._nodes = nodes


    """ replaced_variables, variable_replacement_order, and replaced_functions can be cleaned up """

    """ Used When replacing variables. Needed to break self.nodes into slices """
    @property
    def variable_replacement_order(self):
        return self._variable_replacement_order
    @variable_replacement_order.setter
    def variable_replacement_order(self, new_order):
        if type(new_order) is not list: raise ValueError("Error! NodeVisitor.variable_replacement_order must be a list")
        self._variable_replacement_order = new_order


    """ Used when replacing variables. Allows for multiple replacement in O(n) with proper replacement, not all possible combinations """
    @property
    def replaced_variables(self):
        return self._replaced_variables
    @replaced_variables.setter
    def replaced_variables(self, replaced_variables):   # Do we even need this cause dict?
        if type(replaced_variables) is not dict: raise ValueError("Error! NodeVisitor.replaced_variables must be a dict")
        self._replaced_variables = replaced_variables


    """ May not be useful as functions should be static blocks. 
        But in the event we allow for diverging function executions, support is already built in """
    @property
    def replaced_functions(self):
        return self.replaced_functions
    @replaced_functions.setter
    def replaced_functions(self, replaced_functions):   # Do we even need this cause set?
        if type(replaced_functions) is not set: return ValueError("Error! NodeVisitor.replaced_functions must be a set")
        self.replaced_functions = replaced_functions


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


    def at_path(self, node = None, path = None):
        """ Returns BY REFERENCE the node a path specified from the node passed in """
        if node is None: node = self._root
        if path is None: path = self._path
        if type(node) is not bashlex.ast.node: raise ValueError("Error! Invalid type. NodeVisitor.at_path(node != bashlex.ast.node)")
        if type(path) is not list: raise ValueError("Error! Invalid type. NodeVisitor.at_path(path != list)")
        for el in path: node = self.child(node, el)
        return node


    def children(self, node = None):
        """ Returns an array of all the children of either the node passed in or the root node of NodeVisitor if none specified. 
            If there are no children, an empty array is returned"""

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
            ie can return the 3rd child of the root node (helpful for path finding) """
        # Could add error conditions here
        if node is None: node = self._root
        children = self.children(node)
        try:
            return children[num]
        except Exception as e:
            print('root:', node)
            print('children:', children)
            raise ValueError('Error! NodeVisitor.child #'+str(num)+' does not exist!')


    def set_children(self, parent=None, children=None):
        """ Takes a parent bashlex.ast.node and an array of bashlex.ast.node children.
            Returns the new node & children combo. Technically, BY REFERENCE not copy """
        if parent is None: parent = self._root
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


    def swap_node(self, root, path, new_child):
        """ This replaces the node at the path specified with the new_child passed in
            both of these actions are BY REFERENCE """
        parent = self.at_path(root, path[:-1])

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
            new_child = self.justify(new_child)
            new_child = self.align(new_child, old_child.pos[0])

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
            if hasattr(root, 'list'):
                num_child_nodes = len(parent.list)
                if num_child_nodes >= path[-1]: 
                    parent.list[path[-1]] = new_child
            elif hasattr(parent,'redirects'):
                child_nodes += 1
                if path[-1] == 0:
                    parent.redirect = new_child
        elif k == 'redirect':
            if isinstance(root.output, bashlex.ast.node):
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

        return root


    def replace(self, qual_fn, qual_fn_args, gen_fn, gen_fn_args):
        """ This function is going to sound really weird but its more useful than you think
        You can pass in a "qualifying function" and its arguments as a dictionary. This function needs to take a node as 
        its first argument. It needs to return true wherever in the ast you'd like to replace a node and false everywhere else. 
        You can pass the node visitor calling .replace() into the qualification function to get information & tooling. 
        Then when it returns positive, the generator function is run. The generator function must also take a node as its first arg. 
        The generator function needs to return an array of nodes that you would like to replace the current node with.
        This function then replaces all nodes specified by the qualifying function with the nodes generated and returns these nodes 
        as an array. 
        """
        
        def apply_fn(node, self, qualification_fn, qualification_args, generation_fn, generation_fn_args):
            if qualification_fn(node, **qualification_args):
                replacement_nodes = generation_fn(node, **generation_fn_args)
                new_nodes = []
                for replacement_node in replacement_nodes:
                    for self_node in self._nodes:
                        new_node = copy.deepcopy(self_node)
                        tmp = self.swap_node(new_node, copy.deepcopy(self._path), replacement_node)

                        new_nodes += [ tmp ]
                self._nodes = new_nodes
                return DONT_DESCEND
            else:
                return CONT

        self.apply(apply_fn, self, qual_fn, qual_fn_args, gen_fn, gen_fn_args)
        return self._nodes


    def remove(self, root=None, path=None):
        """ Removes the node at path specified from root's tree. Passed in by reference 
            and returned for good measure. """
        if root is None: root = self._root
        if type(root) is not bashlex.ast.node: raise ValueError("Error! NodeVisitor.remove(root != bashlex.ast.node)")
        if type(path) is not list: raise ValueError("Error! NodeVisitor.remove(path != list)")
        parent = root
        for i in path[:-1]: parent = self.child(parent, i)
        p_vstr = NodeVisitor(parent)
        new_children = p_vstr.children()[:path[-1]] + p_vstr.children()[path[-1]+1:]
        p_vstr.set_children(parent, new_children)
        return root


    def align(self, node = None, delta = None):
        """ This function shifts the pos attr of all nodes in self._root or node passed in by delta
            BY REFERENCE and returns the node for good measure """
        if node is None: node = self._root
        if type(node) is not bashlex.ast.node: raise ValueError("Error! NodeVisitor.align(node != bashlex.ast.node)")
        if type(delta) is not int: raise ValueError("Error! NodeVisitor.align(delta != int)")
        def adjust_pos(node, delta):
            start = (node.pos[0] + delta) if ((node.pos[0] + delta) > 0) else 0
            node.pos = ( start, node.pos[1] + delta )
            return CONT
        NodeVisitor(root=node).apply(adjust_pos, delta)    
        #return NodeVisitor(root=node).apply(adjust_pos, delta).root
        return node


    def justify(self, node = None):
        """ This function shifts the ast so it starts at zero. Basic wrapper around align. """
        if node is None: node = self._root
        if type(node) is not bashlex.ast.node: raise ValueError("Error! NodeVisitor.justify(node != bashlex.ast.node)")
        return NodeVisitor(node).align(delta = -node.pos[0])




def expand_ast_along_path(root, path_to_update, delta):
    """ This function expands the pos attribute to the right along a path by amount delta. Useful for variable replacement & updating.
        Updates the value BY REFERENCE """
    if type(root) is not bashlex.ast.node: raise ValueError('Error! bashparse.ast.expand_ast_along_path(node != bashparse.node)')
    if type(path_to_update) is not list: raise ValueError('Error! bashparse.ast.expand_ast_along_path(path != list)')
    if type(delta) is not int: raise ValueError('delta must be an int')
    def apply_fn(node, delta): node.pos = (node.pos[0], node.pos[1] + delta)
    return NodeVisitor(root).apply_along_path(apply_fn, path_to_update, delta).root




def shift_ast_right_of_path(node, path_to_update, delta):
    
    if type(node) is not bashlex.ast.node: raise ValueError('node must be a bashparse.node')
    if type(path_to_update) is not list: raise ValueError('path_to_update must be a list')
    if type(delta) is not int: raise ValueError('delta must be an int')

    def apply_fn(node, delta):
        new_start = node.pos[0] + delta if ((node.pos[0] + delta > 0) and (node.pos[0] != 0)) else 0
        new_end = node.pos[1] + delta
        node.pos = (new_start, new_end)
    return NodeVisitor(node).apply_right_of_path(apply_fn, path_to_update, delta).root
