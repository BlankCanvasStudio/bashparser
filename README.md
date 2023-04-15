# bashparser: A python library for bash file interpretation

<br/>

# Dependencies
    This package only depends on bashlex

<br/>

# Definitions
- Node: The AST representation of a line of bash code
- Line of Bash Code: Any sequece of valid bash which, when typed into the terminal, will return a fresh command entry line without a parsing error

<br/>

# Usage
ast.py

The funamental "unit" used in this package is the node, the AST of a valid line of bash code.

You can create and print bashparser nodes as follow:
    
    import bashparser

    bash_code = "Echo Hello World"
    nodes = bashparser.parse(bash_code)

    for node in nodes:
        print(node.dump())


bashparser.parse() will parse text input text and return a node for each line present in the text. bashparser.parse() will always return an array of nodes, even if only 1 line of code is provided. 

Manipulating these nodes can be cumbersome and unintuitive, due to the grammar of the bash langauage. This package eases this learning curve by introducing the NodeVisitor object. 

A NodeVisitor should be associated with a single node, specified in the NodeVisitor declaration, and can be accessed via the 'root' property. 

You delcare a NodeVisitor as follows:

    import bashparser
    from bashparser import NodeVisitor

    bash_code = "Echo Hello World"
    nodes = bashparser.parse(bash_code)

    vstr = NodeVisitor(nodes[0])

NodeVisitors can also help convert nodes back into their string form as follows:

    import bashparser
    from bashparser import NodeVisitor

    bash_code = "Echo Hello World"
    node = bashparser.parse(bash_code)[0]

    vstr = NodeVisitor(node)
    bash_code_2 = str(vstr)
    
    print(bash_code_2)

Which returns "Echo Hello World", truly thrilling. This is very helpful for converting modified asts into their string forms, as they are significantly easier to understand. 

bashparser also helpfully creates a command 'unroll' in ~/.local/bin which can be call from the CLI to show the commands executed for a given bash script. 

For example,

    $ echo "for i in 1 2 3 4; do echo \$i; done" > bash_code.sh

    $ unroll --file bash_code.sh

Outputs,

    echo 1
    echo 2
    echo 3
    echo 4

Showing that the 4 commands run during the execution of this file.

<br/>
<br/>

# AST Children

All nodes can have children, tucked into various attributes such as 'list', 'part', and 'command', amoung others. bashparser alleviates the need to remember all these attributes and which nodes they belong to with the Nodevisitor.children(), NodeVisitor.child(), and NodeVisitor.set_children() functions.

**NodeVisitor.children(node = None)** : Returns an array of child nodes which are nested under the node passed in. If no node is specified, the root node of the NodeVisitor is used instead.

**NodeVisitor.child(node = None, num = 0)** : Returns a single child node nested under the node passed in at position num. If no node is specified, the root node of the NodeVisitor is used. 

**NodeVisitor.set_children(parent=None, children=None)** : Takes an array of nodes and optional parent node. Updates the correct child attribute of the parent to the specified children. If no parent node is specified, the root node is used.


<br/>
<br/>

# NodeVisitor.apply(func, *args, **kwargs)
By far the biggest improvement the bashparser package introduces is the funciton NodeVisitor.apply(). This function allows users to easily write custom functions to apply to the ast. In fact, its the funciton which underlies almost all the other functionality introduced in this package. The basic premise of the apply function is it provides the user with the ability to call any function on every node in the graph.

The arguments to the apply function are:

- a function to be called on every node
- optional arguments passed to the function


**Function Definition**

The function passed into the apply function have 2 requirements. First, **the function must take the current node its operating on as its first argument**. And second, the function should return any of the following return values: 

- bashparser.CONT (return this value to continue iterating down the AST)
- bashparser.HALT (return this value to stop iterating the tree immediately)
- bashparser.DONT_DESCEND (return this value to prevent the function from iterating over the children of the current node)

That is to say, functions passed into NodeVisitor.apply should have the form:

    def apply_fn(node, a b, c):
        return bashparser.CONT

**Use Cases**

The apply function can be used however you'd like, but there are a few facilities built into bashparser to encourage a specific programming paradigm. Many of you are probably familiar with this paradigm: the finite state machine. 

When building finite state machines to iterate over and manipulate the AST, one of the first things you will want to do is replace nodes in the AST. This can be done very simply with the NodeVisitor.swap_node() function, but for the sake of example we will talk through using NodeVisitor.apply() to do this replacement. 

Lets say, for the sake of example, you'd like to replace 1 deeply nested node in the AST with 2 different nodes and return both of these results. bashparser has the facilities to do this with the apply function for any node combinations you could imagine. But creating a generalized algorithm comes with one major issue: how do you navigate two different trees that could have very different structures after replacement? The answer: **you don't**. Instead, bashparser opts to naviagate only to nodes present in the original AST used in the NodeVisitor declaration. If you'd like to traverse the new trees nodes, create a new NodeVisitor. This is a very fundamnetal aspect of the bashparser package mentioned above: **A NodeVisitor is declared for a single ast**. 

To get around this limitation the NodeVisitor comes with 3 handy attributes: the NodeVisitor.path() property, the NodeVisitor.nodes() getter, and the NodeVisitor.nodes() setter. The NodeVisitor.path() property will tell you where in the AST you are currently located (relative to the original AST). And the NodeVisitor.nodes() getter and setter can be used to manage diverging AST with ease. 

An incredibly useless, but nonetheless informative, implementation of this program could look something like this:

    import bashparser, copy

    def apply_fn(node, vstr, path, new_nodes):
        if vstr.path === [ 1, 2 ]:
            vstr.nodes = []
            node_copies = [ copy.deepcopy(vstr.root), copy.deepcopy(vstr.root) ]
            for i, nc in enumerate(node_copies):
                vstr2 = bashparser.NodeVisitor(nc)
                vstr2.swap_node(new_nodes[i])
                vstr.nodes += [ vstr2.root ]
    
    vstr1 = bashparser.NodeVisitor(node)
    vstr1.apply(apply_fn, vstr1, some_path, some_new_nodes)
    
    for node in vstr1.nodes():
        print(node.dump())

This example is poorly written but shows NodeVisitor.apply(), NodeVisitor.path(), and NodeVisitor.nodes() being used to swap the node at [1,2] with the root node of the original ast. 

For a significantly more useful example, the implementation of the __str__ property is listed below: 

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

If you would like to see a more complex example, which actively highlights why the package was built in this way, I recommend reading bashparser.variables.replace_variables. Its an algorithm for arbitrary variable replacement in bashscripts and hightlights the importance of these different features. 

<br/>

# NodeVisitor Function Descriptions

With this detail description of the apply function out of the way, now its time for the easy part of the documentation: function descriptions. NodeVisitors are instantiated relative to a single AST, as such all of these functions act on and update the root node by default. It can, however, be useful to call these functions on a single node without declaring a new NodeVisitor. To help with this, most functions take a 'root' parameter which can be used in place of NodeVisitor.root. This is not a feature for NodeVisitor.apply() or any variations on the apply function listed below.  

**NodeVisitor.parent()** - A useful but dangerous property. In apply() it can be used to return the current parent if the NodeVisitor is passed into the function.

**NodeVisitor.apply(apply_fn, \*args, \*\*kwargs)** - This function tries to run apply_fn(*args, **kwargs) on every node in the ast using a depth first search (L to R). By returning CONT, DONT_DESCEND, or HALT from apply_fn you can affect the traversal through the ast (details above). 

**NodeVisitor.apply_along_path(apply_fn, path, \*args, \*\*kwargs)** - Applies a function along a path. Acts just like apply but on a path 

**NodeVisitor.apply_right_of_path(apply_fn, path, \*args, \*\*kwargs)** - Like apply but it only acts on the right side of the path specified. Exclusive of the path itself 

**NodeVisitor.apply_left_of_path(apply_fn, path, \*args, \*\*kwargs)** -  Like apply but it only acts on the left side of the path specified. Exclusive of the path itself 

**NodeVisitor.at_path(root = self.root, path=self.path)** - Returns BY REFERENCE the node a path specified from the root passed in 

**NodeVisitor.children(root = self.root)** - Returns an array of all the children of either the root passed in or the root node of NodeVisitor if none specified. If there are no children, an empty array is returned

**NodeVisitor.child(root = self.root, num = 0)** - Returns the child with number specified by argument (ie can return the 3rd child of the root node (helpful for path finding))

**NodeVisitor.set_children(root = self.root, children = [])** - Takes a root bashlex.ast.node and an array of bashlex.ast.node children. Returns the new node & children combo. Technically, BY REFERENCE not value

**NodeVisitor.swap_node(child, root = self.root, path = self.path)** - This replaces the node at the path specified with the child passed in both of these actions are BY REFERENCE

**NodeVisitor.replace(qual_fn, qual_fn_args, gen_fn, gen_fn_args)** - This function is going to sound really weird but its more useful than you think. You can pass in a "qualifying function" and its arguments as a dictionary. This function needs to take a node as its first argument. It needs to return true wherever in the ast you'd like to replace a node and false everywhere else. You can pass the node visitor calling .replace() into the qualification function to get information & tooling. Then when it returns positive, the generator function is run. The generator function must also take a node as its first arg. The generator function needs to return an array of nodes that you would like to replace the current node with. This function then replaces all nodes specified by the qualifying function with the nodes generated and returns these nodes as an array.

**NodeVisitor.remove(root = self.root, path = None, child = child at current path)** - Removes the node at path specified from root's tree. Passed in by reference and returned for good measure. If a child is specified, then the path passed in is used to identify the parent node, refered to as A. If any of the children of A are equal to the node passed in as the child parameter, they are removed.

**NodeVisitor.align(root = self.root, delta = None)** - This function shifts the pos attr of all nodes in self._root or node passed in by delta BY REFERENCE and returns the node for good measure

**NodeVisitor.justify(root = self.root)** - This function shifts the ast so it starts at zero. Basic wrapper around align.


<br/>

# Other Package Function Descriptions

All of the above NodeVisitor functions which take an optional root argument are also aliased to be run with the form:

    import bashparser
    from bashparser import X, parse
    
    node = parse('echo "Its an example"')[0] 
    
    X(root=node)

Their descriptions aren't repeated here for the sake of brevity. Instead, other useful functionality, not assiciated with the node visitor is listed below. The commands are organized into the following subsections: ast, commands, functions, variables, unroll, complexity, template, chunk, and generalize. 

This organization mirrors the packages files, if you care to contribute.


<br/>

# AST

**expand_ast_along_path(root, path_to_update, delta)** - This function expands the pos attribute of the nodes, used to specify the string indexes between which the nodes occur, to the right along a path by amount delta. Useful for variable replacement & updating. Updates the value BY REFERENCE

**shift_ast_right_of_path(root, path_to_update, delta)** - Takes a root and adds the delta to both pos attributes if its to the right of the path. Excludes the path. Functions BY REFERENCE not value but returns the root for posterity sake



<br/>

# COMMANDS

**build_alias_table(nodes, alias_table = {})** - Takes an array of nodes, checks to see if its moving a file. If it is, you could be using command aliasing. These aliases get recorded in alias_table dict. In the event there is nested aliasing, the value in the alias table is the most nested value (if that makes sense). Acts BY REFERENCE and returns for good measure. Can be used to expand already existing alias table


**resolve_aliasing(nodes, alias_table = {})** - This function replaces the command text of any command alias specified in the alias table with the name of the function truly being executed.


**build_and_resolve_aliasing(nodes, alias_table={})** - A helpful wrapper so building and resolving can be done over a number of nodes at once while still preserving internal order of aliasing 



<br/>

# FUNCTIONS

**build_fn_table(nodes, fn_dict={})** - Iterates over the nodes looking for any function definitions. If one is found its added to the function dictionary with index of funciton name and a value of the list node present in between the brackets. This allows for eaier argument replacement later (pass in list node rather than array of commands). Returns the function dictionary for good measure but acts BY REFERENCE 

**resolve_functions(nodes, fn_dict, var_list = None)** - Iterates over nodes, replacing any functions with their corresponding code and replacing any variables as well (including parameters passed into the function)


**build_and_resolve_fns(nodes, fn_dict = {}, var_list = None)** - a helpful wrapper so the above functions can be done in a single step 



<br/>

# VARIABLES

**replace_variables(nodes, var_list, replace_blanks=False)** - Takes a node, var list. Replaces all the instances of variables found in the var_list with their corresponding value via regex. **var_list IS NOT UPDATED WITH VALUES IN NODE. USE substitute_variables FOR THAT FUNCITONALITY.** The identification of a variable is done via the presence of a parameter node, thus if none are present, nothing will be replaced, even if a $name is present in text of a nodes. If replace_blanks is True, all parameter nodes not present in the var_list will be removed and the $name will be replaced with a blank. If replace_blanks is False and the variable isn't present in the var_list, no replacement occurs. This means the nodes returned are all valid bashlex nodes. This function also properly shifts the ast to account for any replacements, meaning you shouldn't be able to tell if the tree has been replaced or was generated directly from the text. You're welcome, it was hell

**substitute_variables(nodes, var_list = {}, replace_blanks=False)** - This function finds and replaces all values found in the list of nodes passed into it. Different from replace_variables which only does the replacement. Returns an array of all the replaced trees. If replace_blanks is True and a variable is enountered which is not present in the var_list, then it is updated with a blank value and the parameter node is remove. If replace_blanks is False and a variable is enocuntered which does not appear in the var_list, it is left as is.

**update_variable_list(nodes, var_list)** - Strips any variables out of ast and saves them to variable list. Returns an updated variable dict

**add_variable_to_list(var_list, name, values)** - Adds the corresponding name and value(s) to dictionary. If name exists in the dictionary, the value is added. Prevents bugs with use of the var_list 

**update_var_list_with_for_loop(for_nodes, var_list, replace_blanks=False)** - This function takes a for_loop node and a variable list. It updated the value of the var_lits with the value that the for loop assigned to the iterator. This value could be a string, another variable, or a command substitution. All cases are covered here. If another variable is specified, the value assigned is a replication of the other variables value at that point in time, not a reference to the other variable (ie in-line replacement also occurs)



<br/>

# UNROLL

The file unroll.py can be called from the CLI passing a --file argument to specify the bash script you wish to unroll. Passing the --cmd flag will return the commands executed without any replacement, ie calling strip_cmd, otherwise advanced_unroll is used

**strip_cmd(nodes)** - Strips all the commands executed from a series of bash nodes in order. No replacement occurs, it simply returns the raw commands.

**advanced_unroll(nodes, var_list={}, fn_dict={}, alias_table={}, strip_cmds=True)** - This function resolves command aliasing, function calls, and variable substitutions in a series of bash nodes, replacing as it progresses. The strip_cmds boolean can be toggeled to return only the commands executed or the replaced nodes. 



<br/>

# COMPLEXITY

This file contians some programs I wrote to quantify the complexity of bash commands and scripts. 

**node_complexity(node)** - returns a 'complexity score' for the node passed in.

**file_complexity(nodes)** - returns a 'complexity score' for the series of nodes passed in (aka a file).

**weighted_file_complexity(nodes)** - returns the complexity score for the series of nodes, divided by the length of the array passed in.

**hashing_complexity(node, commands = [])** - returns the complexity score of each unique template found in the given node (see templating below)

**file_hashing_complexity(nodes)** - returns the complexity score of each unique template found in a series of bash nodes (aka a file).

**weighted_file_hashing_complexity(nodes)** - returns the complexity score of each unique tempalte found in a series of bash nodes, divided by the number of nodes.



<br/>

# CHUNK

The Chunk is an abstraction of the 'basic block' common in most assembler techniques. A chunk has a name, a start, and an end. The name is simply a string and the start and end are paths to the beginning of the chunk. A chunk can be declared as follows:

    from bashparse import Chunk
    
    name='some name
    start = [1,2]
    end = [2,1]

    tmp = Chunk(name, start, end)

A ChunkConnection is an object used to denote when two chunks are linked in some way, in the case of this package its either physical overlap, or they contian similar variables.

bashparser can create 2 kinds of chunks, 'variable chunks' and 'cd chunks'. A variable chunk is the region where a particular variable definition is used and a cd chunk is a section of code executed in a particular directory.

**find_variable_chunks(nodes)** - returns a list of all the variable chunks in the array of nodes

**find_cd_chunks(nodes)** - returns a list of all cd chunks in the array of nodes

**is_connected(chunk_one, chunk_two)** - determines if two chunks are connected

**return_connected_chunks(chunks)** - returns a list of all connected chunks

**return_dependent_chunks(connected_chunks, orig_nodes)** - returns a list of all the chunks which need to occur in order



<br/>

# GENERALIZE

bashparser also provides the facilities to convert bash nodes into their more 'generalized form'. FOr example the lines:

    echo this

and 

    echo that

both have the same general form:

    echo %d

as they are both simply echoing a string.

One can easily envision how this generalization becomes a difficult task in the limit of complex bash code. Luckily, I did that for you.

The list of possibile datatypes arguments can be generalized to are:

    %d - data / undefined
    %f - flag
    %s - command substitutions
    %v - variable
    %u - URL
    %p - path

To generate these generalizations bashparser offers the following functions:

**basic_generalization(generalize_nodes)** - This function takes an array of nodes and simply replaces all the arguments with their corresponding data types

**parameter_tracking_generalization(generalize_nodes, params_used = {}, param_num = 0)** - This function generalizes all the parameters of the nodes passed in, using a number to identify each parameter used. If a parameter is repeated later in the code, it will have the name number. The starting parameter number is specified with param_num and params_used in a dictionary which indexes by the parameter string and returns the parameter number.

**variable_tracking_generalization(generalize_nodes, params_used = {}, param_num = 0)** - This replaces all variable uses with a unique parameter number for each parameter name. Same as parameter_tracking_generalization above but specifically tracking the variables in the script


<br/>

# TEMPLATE


**class Tamplate(text = '', chunks = [None], ratio = -1, raw_count = 1)**

A Template builds on the concept of a chunks and generalization by allowing users to group multiple generalized chunks together. A template contains the accociated text, the generalized chunks, the number of occurances, and the 'ratio.' The ratio user defined but is most useful when its the length of the template divided by the length of the file.

To aid in building these templates, bashparser offers the following functions:

**generate_templates(nodes)** - Takes an array of nodes, finds all variable and cd chunks, generalized each chunk, and returns all unique associated chunks

**add_templates(templates, template_record)** - This function takes in the templates & current template records and returns the updated template_record object. This exists mostly so users don't have the really think about the data type manipulation

**templatize(nodes, template_record = {})** - This function takes a list of nodes and a pre-existing template record, unrolls the nodes (with full in-line variable, command, and function replacement), and runs generate templates on the raw, replaced, and unrolled nodes. Any unique templates are added to the template record and returned
