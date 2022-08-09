# bashparse: A python library for bash file interpretation

bashparse is a python library containing a number of helpful tools to analyze bash scripts.

## Dependencies

    This package only depends on bashlex

## Usage

ast.py

The first and most important object to understand is the NodeVisitor. This object is used to manipulate bashlex.ast.node objects. Bashlex.ast.nodes are a single construct from the bash programming language. If a single command is issued, then the node will be just that command. If a for loop is used, then a node will be the entire for loop and any command executed in the body of that loop.

A NodeVisitor is declared using the syntax: var_name = NodeVisitor(root) where root is the bashlex.ast.node you would like to manipulate. 

When converted to a string, the NodeVisitor prints a formatted version of the root specified during the declaration.

The most imporant property of the node visitor is the apply() function. apply() takes the function you would like to execute on every node in NodeVisitor.root as its first argument and any further arguments passed in will be passed into the function you defined using *args and **kwargs.
This function can do anything but the easiest implementation is usually a FSM. It allows you to easily extract and manipulate data within the ast, while abstracting far enough away from the ast that you don't need to worry about writing graph algorithms. apply() comes with 3 return values which allow users to manipate the traversal of the tree. If your defined function returns bashparse.ast.CONT (or nothing), apply() will continue iterating over the tree. If bashparse.ast.DONT_DESCEND is returned, apply() will continue execute but will skip all children of the current node. If bashparse.ast.HALT is returned, apply() will return immediately without visiting any other nodes. 

The functions you tend to write will result in a multitude of different ASTs. A simple example of this is for loop iterator replacement. Replacing the values in "for i in (a b c)" returns 3 asts with i=a,i=b, and i=c. In a much more complex senario, like nested for loops, one can see how quickly the problem becomes non-trivial. To cope with this, a very simple approach is taken: you will traverse over the given root node and index relative to this root node. This means you can have consistent indexing even with divergent ast manipulationg paths. The NodeVisitor.nodes are actually whats operated on and when multiple nodes are returned from a function, it is simply returning NodeVisitor.nodes. If the operation cannot return multiple ASTs then the operation is performed on NodeVisitor.root or a node passed in as an argument. 
The reason for doing this is that the divergent trees make it difficult to talk about arbitrarily branching paths, all occuring somewhat simultaneously. This means when you replace a node, it must be the final version of the node, as it will not be visited during that iteration of the apply() function. 
The apply function comes in 3 helpful variants: apply_along_path, apply_left_of_path, and apply_right_of_path. These functions can be built with the apply function but are useful enough to be included separately.

The NodeVisitor allows you to return specific nodes, by reference, from the NodeVisitor.root object using the at_path() member function. You can also pass in a node you would like to draw from by specifying the node parameter on call. 
The NodeVisitor can return the children of the root node or a specified node with the function children(). This has an optional node parameter, which will be used over NodeVisitor.root when returning children. 
The NodeVisitor also gives a number system to the children, allowing you to refer to child #3 consistently and without concern for how the nodes are nested under the parent. 
The set_children() function allows the children of a node to be set. If no parent is passed in, then NodeVisitor.root is assumed to be the parent referenced.
The swap_node function allows the user to switch a node at a specfied path of the passed in root with a node also passed into the function. This function will automatically adjust the pos attribute of the nodes, so no user intervention is needed to create a valid AST.

The replace function: This function is going to sound really weird but its more useful than you think. You can pass in a "qualifying function" and its arguments as a dictionary. This function needs to take a node as its first argument. It needs to return true wherever in the ast you'd like to replace a node and false everywhere else. You can pass the node visitor calling .replace() into the qualification function to get information & tooling. Then when it returns positive, the generator function is run. The generator function must also take a node as its first arg. The generator function needs to return an array of nodes that you would like to replace the current node with.This function then replaces all nodes specified by the qualifying function with the nodes generated and returns these nodes as an array.

The remove() function can be used in 2 two ways. First, if no child is specified then the node at the end of the path specified will be removed from the AST. If a child is specified, then the path is assumed to be to the parent and the first child which matches that node will be removed. 

The align funciton adjusts the pos attribute of all nodes by the amount specified in delta.

The justify function shifts the AST so that it starts from zero.

expand_ast_along_path applies align along a uer justified path. 

shift_ast_right_of_path applies align to the right of the specified path



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