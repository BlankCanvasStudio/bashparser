# bashparse: A python library for bash file interpretation

<br/>

# Dependencies
    This package only depends on bashlex

<br/>

# Definitions
- Node: The AST representation of a line of bash code
- Line of Bash Code: Any sequece of valid bash which, when typed into the terminal, will return a fresh command entry line

<br/>

# Usage
ast.py

The funamental "unit" used in this package is the node, the AST of a valid line of bash code.

You can create and print bashparse nodes as follow:
    
    import bashparse

    bash_code = "Echo Hello World"
    nodes = bashparse.parse(bash_code)

    for node in nodes:
        print(node.dump())


bashparse.parse() will parse text input text and return a node for each line present in the text. bashparse.parse() will always return an array of nodes, even if only 1 line of code is provided. 

Manipulating these nodes can be cumbersome and unintuitive, due to the grammar definitions used in the bash langauage. This package eases this learning curve by introducing the NodeVisitor object. 

A NodeVisitor should be associated with a single node, specified in the declaration. The node can be accessed via the 'root' property of the NodeVisitor. 

You delcare a NodeVisitor as follows:

    import bashparse

    bash_code = "Echo Hello World"
    nodes = bashparse.parse(bash_code)

    vstr = NodeVisitor(nodes[0])

NodeVisitors can also help convert nodes back into their string form as follows:

    import bashparse
    from bashparse import NodeVisitor

    bash_code = "Echo Hello World"
    node = bashparse.parse(bash_code)[0]

    vstr = NodeVisitor(node)
    bash_code_2 = str(vstr)
    
    print(bash_code_2)

Which returns "Echo Hello World", truly thrilling. This is very helpful for converting modified asts into their string forms, as they are significantly easier to understand. 

<br/>
<br/>

# AST Children

All nodes can have children, tucked into various attributes such as 'list', 'part', and 'command', amoung others. Bashparse alleviates the need to remember all these attributes and which nodes they belong to with the Nodevisitor.children(), NodeVisitor.child(), and NodeVisitor.set_children() functions.

**NodeVisitor.children(node = None)** : Returns an array of bashlex nodes which are nested under the specified node. If no node is specified, the root node of the NodeVisitor is used instead.

**NodeVisitor.children(node = None, num = 0)** : Returns a single node nested under node at position num. If no node is specified, the root node of the NodeVisitor is used. 

**NodeVisitor.set_children(parent=None, children=None)** : Takes array of children nodes and optional parent node. Updates the correct child attribute of the parent to the specified children. If no parent node is specified, the root node is used.


<br/>
<br/>

# NodeVisitor.apply(func, *args, **kwargs)
By far the biggest improvement the bashparse package introduces is the funciton NodeVisitor.apply(). This function allows users to easily write custom functions to apply to the ast. In fact, its the funciton which underlies all the other functionality introduced in this package. The basic premise of the apply function is it provides the user with the ability to call any function on every node in the graph.

The arguments to the apply function are:

- a function to be called on every node
- optional arguments passed to the function


**Function Definition**

The function passed into the apply function have 2 requirements. First, **the function must take the current node its operating on as its first argument**. And second, the function should return any of the following return values: 

- bashparse.CONT (return this value to continue iterating down the AST)
- bashparse.HALT (return this value to stop iterating the tree immediately)
- bashparse.DONT_DESCEND (return this value to prevent the function from iterating over the children of the current node)

**Use Cases**

The apply function can be used however you'd like, but there are a few facilities built into bashparse to encourage a specific programming paradigm. Many of you are probably familiar with this paradigm: the finite state machine. 

When building finite state machines to iterate over and manipulate the AST, one of the first things you will want to do is replace nodes in the AST. This can be done very simply with the NodeVisitor.swap_node() function, but for the sake of example we will talk through using NodeVisitor.apply() to do this replacement. 

Lets say, for the sake of example, you'd like to replace 1 deeply nested node in the AST with 2 different nodes and return both of these results. Bashparse has the facilities to do this with the apply function for any node combinations you could imagine. But creating a generalized algorithm comes with one major issue: how do you navigate two different trees that could have very different structures after replacement? The answer: you don't. Instead, bashparse opts to naviagate only to nodes present in the original AST using in the NodeVisitor declaration. If you'd like to traverse the new trees nodes, please create a new NodeVisitor. This is a very fundamnetal aspect of the bashparse package mentioned above: A NodeVisitor is declared for a single ast. 

To get around this limitation the NodeVisitor comes with 3 handy attributes: the NodeVisitor.path() property, the NodeVisitor.nodes() getter, and the NodeVisitor.nodes() setter. The NodeVisitor.path() property will tell you where in the AST you are currently located (relative to the original AST). And the NodeVisitor.nodes() getter and setter can be used to manage diverging AST with ease. 

An incredibly useless, but nonetheless informative, implementation of this program could look something like this:

    import bashparse, copy

    def apply_fn(node, vstr, path, new_nodes):
        if vstr.path === [ 1, 2 ]:
            vstr.nodes = []
            node_copies = [ copy.deepcopy(vstr.root), copy.deepcopy(vstr.root) ]
            for i, nc in enumerate(node_copies):
                vstr2 = bashparse.NodeVisitor(nc)
                vstr2.swap_node(new_nodes[i])
                vstr.nodes += [ vstr2.root ]
    
    vstr1 = bashparse.NodeVisitor(node)
    vstr1.apply(apply_fn, vstr1, some_path, some_new_nodes)
    
    for node in vstr1.nodes():
        print(node.dump())

This example is very poorly written but shows how the NodeVisitor.apply(), NodeVisitor.path(), and NodeVisitor.nodes() properties can be used. For a significantly more useful example, the implementation of the __str__ property is listed below: 

    def __str__(self):
        """ Don't let it save itself, always recompute. Much easier than changing every time """
        self._string = ""
        
        def apply_fn(node):
            k = node.kind
            word = ''
            if node.kind in self.passable_nodes: return CONT
            elif node.kind == 'operator': word = node.op
            elif node.kind == 'pipe': word = node.pipe
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
                print('node: ', node.dump())
                raise ValueError('Error! Unsupported node kind encountered when converting NodeVisitor to string: ', node.kind)
            self._string = self._string + word + ' '
            return CONT

        self.apply(apply_fn)
        return self._string[:-1]     # remove trailing space cause wrong

If you would like to see a more complex example, which actively highlights why the package was built in this way, I recommend reading bashparse.variables.replace_variables. Its an algorithm for arbitrary variable replacement in bashscripts and hightlights the importance of these different features. 

<br/>

# NodeVisitor Function Descriptions

With this detail description of the apply function out of the way, now its time for the easy part of the documentation: function descriptions. NodeVisitors are instantiated relative to a single AST, as such all of these functions act on and update the root node by default. It can, however, be useful to call these functions on a single node without declaring a new NodeVisitor. To help with this, most functions take a 'root' parameter which can be used in place of NodeVisitor.root. This is not a feature for NodeVisitor.apply() or any variations on the apply function listed below.  

**NodeVisitor.parent()** - A useful but dangerous property. In apply() it can be used to return the current parent if the NodeVisitor is passed into the function.

**NodeVisitor.apply(apply_fn, \*args, \*\*kwargs)** - This function tries to run apply_fn(*args, **kwargs) on every node in the ast using a depth first search (L to R). By returning CONT, DONT_DESCEND, or HALT from apply_fn you can affect the traversal through the ast. 

**NodeVisitor.apply_along_path(apply_fn, path, \*args, \*\*kwargs)** - Applies a function along a path. Acts just like apply but on a path 

**NodeVisitor.apply_right_of_path(apply_fn, path, \*args, \*\*kwargs)** - Like apply but it only acts on the right side of the path specified. Exclusive of the path itself 

**NodeVisitor.apply_left_of_path(apply_fn, path, \*args, \*\*kwargs)** -  Like apply but it only acts on the left side of the path specified. Exclusive of the path itself 

**NodeVisitor.at_path(root = self.root, path=self.path)** - Returns BY REFERENCE the node a path specified from the root passed in 

**NodeVisitor.children(root = self.root)** - Returns an array of all the children of either the root passed in or the root node of NodeVisitor if none specified. If there are no children, an empty array is returned

**NodeVisitor.child(root = self.root, num = 0)** - Returns the child with number specified by argument (ie can return the 3rd child of the root node (helpful for path finding)

**NodeVisitor.set_children(root = self.root, children = [])** - Takes a root bashlex.ast.node and an array of bashlex.ast.node children. Returns the new node & children combo. Technically, BY REFERENCE not copy

**NodeVisitor.swap_node(child, root = self.root, path = self.path)** - This replaces the node at the path specified with the child passed in both of these actions are BY REFERENCE "

**NodeVisitor.replace(qual_fn, qual_fn_args, gen_fn, gen_fn_args)** - This function is going to sound really weird but its more useful than you think You can pass in a "qualifying function" and its arguments as a dictionary. This function needs to take a node as its first argument. It needs to return true wherever in the ast you'd like to replace a node and false everywhere else. You can pass the node visitor calling .replace() into the qualification function to get information & tooling. Then when it returns positive, the generator function is run. The generator function must also take a node as its first arg. The generator function needs to return an array of nodes that you would like to replace the current node with. This function then replaces all nodes specified by the qualifying function with the nodes generated and returns these nodes as an array.

**NodeVisitor.remove(root = self.root, path = None, child = child at current path)** - Removes the node at path specified from root's tree. Passed in by reference and returned for good measure. If a child is specified, then the path is actually to the parent. The child which matches the child passed in is then removed. 

**NodeVisitor.align(root = self.root, delta = None)** - This function shifts the pos attr of all nodes in self._root or node passed in by delta BY REFERENCE and returns the node for good measure

**NodeVisitor.justify(root = self.root)** - This function shifts the ast so it starts at zero. Basic wrapper around align.


commands.py

Because you can move files in bash, people can frequently obfuscate what command they are executing by changing the name. This means that people will need to read the file to find any underlying context. This process can and is automated away in command.py. The first step is to build an alias_table, which is simply a dictionary. The alias table tracks any instances of mv x y or cp x y and records it. In the event of multiple nesting in this format, the alias is resolved and saved as the actual command which will be executed. 
After building the alias table, you can resolve_aliasing, which will change all commands executed back to the original filename being executed. 


functions.py

if one wants to find and replace all the functions used in a bash script all they need to do is to build the function table using build_fn_table on the node which contains a function and the resolve_functions() on the node to be replaced. If you pass a node which neither contains, nor defines a function then the node will be passed back without modification. So calling this on a series of nodes in a row is a perfectly valid application. The function build_and_resolve_fn is a useful wrapper of the above process which takes an array of nodes to iterate over and automates the process.


variables.py 

This package also allows for the tracking and repalcement of variables in bashlex.ast.nodes. The first step in this process is to build the variable list using update_variable_list(node, var_list=dict). Then the variables can be replaced using replace_variables(). If you want to manually add entries to the dictionary use add_variable_to_list().  


unroll.py

This file provides 2 key pieces of functionality. It provides the ability to strip all the commands executed from an array of bashlex.ast.nodes using the strip_cmd() function. This simply gathers and returns all the commands executing in those nodes. If statements are returned as a unit, as there is no current functionality to determine the outcome of that branch. functions are also returned as a unit and no replacements occur. For a more advanced command stripping, which tracks variables, resolves functions, and resolves any aliasing use advanced_unroll(). You can also specify a var_list, fn_dict, and alias_table to be used in this function.  



-----------------

Lets assume that you'd like to get all the commands executed from the following bash script:
        
    n="/tmp /var /etc"
    for a in $n
    do
        cd $a
        touch somefile.txt
    done
    
We want to unroll this loop, replace all the variables, and return these commands as strings. 
    
To do this we can do the following:
    
    import bashparse
    bash_text = 'n="/tmp /var /etc"\n for a in $n \n do \n cd $a \n touch somefile.txt \n done'
    nodes = bashparse.parse(bash_text)  # Parse the text
    commands_executed = bashparse.advanced_unroll(nodes)

    for command in commands_executed:  # Print the command nodes as string
        print(bashparse.convert_tree_to_string(command))
    
This will return the following output:
    
    n=/tmp /var /etc
    touch somefile.txt
    cd /etc
    touch somefile.txt
    cd /var
    touch somefile.txt
    cd /tmp
    touch somefile.txt
    cd /etc
    touch somefile.txt
    cd /var
    touch somefile.txt
    cd /tmp
    
Which is easily seen to be the code actually executed by the script, in the order that its displayed.
    
One could easily find all the directories the script tries to enter using the following code:
        
    import bashparse
    from bashparse import NodeVisitor
    def apply_fn(node, vstr):
        if node.kind == 'command':
            # format is cd there
            if node.parts[0].word == 'cd':
                vstr.directories += [ node.parts[1].word ]  # this would be "there" in the example format
        return CONT
    vstr = NodeVisitor(node)
    vstr.directories = []
    vstr.apply(apply_fn, vstr)
    directories_entered = vstr.directories

    for directory in directories_entered:
        print(directory)
    
Which would return the output:
    
    /var
    /tmp
    /etc
      

## Practice Implementations:
    
- **update_variable_list_with_node(node: bashlex.ast.node, var_list: dict):** This function finds any variable declarations in the abstract syntax tree(s) and saves the name value pair to the dictionary passed in, such that you can index the dictionary by variable name and return the variable's value. Note, the variables value will always be saved as an array.
    - Takes: node object and variable dictionary
    - Returns: Variable dictionary

    import bashparse
    def update_variable_list_with_node(node, var_list={]}):
        def apply_fn(node, var_list):
            if node.kind == 'assignment':
                var_list = bashparse.update_variable_list(node, var_list)
            return CONT
        vstr = bashparse.NodeVisitor(node)
        vstr.apply(apply_fn, var_list)
        return var_list


- **find_specific_commands(node: bashlex.ast.node, commands_looking_for: list of str, saved_command_dictionary: dict):** This function checks the ast for exections of commands listed in the commands_looking_for. If the command is found in the ast(s) then the path to that node is added to the index in saved_command_dictionary.
    - Takes: node object, list of commands to look for (a list of strings), a dictionary to save the commands to, and a bool identifying if the commands should be saved as nodes or strings
    - Returns: the updated command dictionary

    import bashparse
    from bashparse import NodeVisitor, CONT, DONT_DESCEND
    def find_specific_commands(node, commands_looking_for, command_index_dictionary):
        def apply_fn(node, vstr, commands_looking_for, command_index_dictionary):
            if node.kind == "command":
                command_word = node.parts[0].word
                if command_word in commands_looking_for:
                    command_index_dictionary[command_word] = vstr.path
                    return DONT_DESCEND
            return CONT
        vstr = NodeVisitor(node)
        vstr.apply(apply_fn, vstr, commands_looking_form, command_index_dictionary)
        return command_index_dictionary

- **return_commands_from_variable_delcaraction(node: bashlex.ast.node):** This function returns any commands that would be executed in a variable declaration via a command substitution. I.e. a=$(wget www.google.com).
    - Takes: node object
    - Returns: list of nodes

    import bashparse
    from bashparse import NodeVisitor, CONT, DONT_DESCEND
    def return_commands_from_variable_declaration(node):
        def apply_fn(node, vstr):
            if node.kind == "assignment" and len(node.parts) and node.parts[0].kind == "commandsubstitution":
                vstr.nodes += [node]
                return bashparse.DONT_DESCEND
            return bashparse.CONT
        vstr = NodeVisitor(node)
        vstr.nodes = []
        vstr.apply(apply_fn, vstr)
        return vstr.nodes

- **return_commands_from_command_substitutions(node: bashlex.ast.node):** This function iterates through the ast to find any command substitutions and returns the commands these substitutions would be executing. 
    - Takes: node object
    - Returns: list of nodes

    import bashparse
    from bashparse import NodeVisitor, CONT, DONT_DESCEND
    def return_commands_from_command_substitutions(node):
        def apply_fn(node, vstr):
            if node.kind ==  "commandsubstitution":
                vstr.nodes += [node.command]
                return bashparse.DONT_DESCEND
            return bashparse.CONT
        vstr = NodeVisitor(node)
        vstr.nodes = []
        vstr.apply(apply_fn, vstr)
        return vstr.nodes

- **return_commands_from_for_loops(node: bashlex.ast.node):** This function looks through node(s) for any for loops and returns all the command nodes in the for loops it finds. 
    - Takes: node object
    - Returns: list of nodes   

    import bashparse
    from bashparse import NodeVisitor, CONT, DONT_DESCEND
    def return_commands_from_for_loops(node):
        def apply_find_for_loops(node, vstr):
            if node.kind != "for": return CONT 

            def return_commands(node, vstr):
                if node.kind == "command": vstr.nodes += [ node ]
                return CONT
            
            tmp_vstr = NodeVisitor(node):
            tmp_vstr.apply(return_commands, tmp_vstr)
            vstr.nodes += tmp_vstr.nodes
        vstr = NodeVisitor(node)
        vstr.apply(apply_find_for_loops, vstr)
        return vstr.nodes

- **shift_tree_pos(node:bashlex.ast.node, shift_amount:int):** This takes node or a list of nodes and the amount to shift all the pos values by. This is used to shift the nodes pos by any given value, instead of its offset in the string. Returns the node with the updated pos values 
    - Takes: node object and the shift amount (int) 
    - Returns: the shifted node object

    def shift_tree_pos(node, shift_amount):
        def apply_fn(node, shift_amt):
            node.pos = (node.pos[0] + shift_amt, node.pos[1] + shift_amt)
            return CONT
        NodeVisitor(node).apply(apply_fn, shift_amount)
        return node

- **shift_tree_pos_to_start(node: bashlex.ast.node / list):** If a single node is provided it shifts the given node's pos to starting at 0. If an array of nodes are given, the first node's pos starts at zero and all following nodes have pos values that follow the node preceding it. A helpful wrapper of the above function. Returns the newly shifted node
    - Takes: node object
    - Returns: the shifted node object

    def shift_tree_pos(node, shift_amount):
        def apply_fn(node, shift_amt):
            node.pos = (node.pos[0] + shift_amt, node.pos[1] + shift_amt)
            return CONT
        shift_amount = node.pos[0]
        if shift_amount:
            NodeVisitor(node).apply(apply_fn, shift_amount)
        return node

- **return_variable_paths(node: bashlex.ast.node):** Should be used to find all the varaibles used in the node. Returns a list of the paths which can be used to identify all the variables in the node.
    - Takes: node object
    - Returns: list of path variables to the variables

    from bashparse import NodeVisitor
    import copy
    def return_variable_paths(node):
        def apply_fn(node, vstr):
            if node.kind == 'parameter':
                vstr.nodes += [ copy.copy(vstr.path) ]
        vstr = NodeVisitor(node)
        vstr.nodes = []
        vstr.apply(apply_fn)
        return vstr.nodes
        

- **return_nodes_of_type(node: bashlex.ast.node, node_type: str):** This function takes a node and a string of the node type one is looking for. This returns the nodes themselves, as opposed to path_variables.
    - Takes: node object and string indicating type looking for
    - Returns: list of node objects

    def return_nodes_of_type(node, node_type:str):
        def apply_fn(node, vstr, node_type):
            if node.kind == node_type: vstr.nodes += [ node ]
            return CONT
        vstr = NodeVisitor(node)
        vstr.nodes = []
        vstr.apply(apply_fn, vstr, node_type)
        return vstr.nodes


- **return_node_at_path(bashlex.ast.node, path_variable or list of ints):** This function naivgates the ast down the path specified in the path argument. It then returns the actual node at that location, rather than a copy as is the case with a lot of other functions in this package.

    def return_node_at_path(node, path):
        vstr = NodeVisitor(None)
        child = node
        for el in path child = vstr.child(child, el)
        return child