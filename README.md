# bashparse: A python library for bash file interpretation

bashparse is a python library containing a number of helpful tools to contextualize bash scripts.

## Dependencies

    This package only depends on bashlex

## Usage
    
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
    replaced_nodes = bashparse.find_and_replace_variables(nodes)  # Make the variable substitutions
    commands_executed = bashparse.return_nodes_of_type(node, 'command')  
    # Get all the commands executed from newly replaced nodes
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
    bash_text = 'n="/tmp /var /etc"\n for a in $n \n do \n cd $a \n touch somefile.txt \n done'
    nodes = bashparse.parse(bash_text)  # Parse the text
    replaced_nodes = bashparse.find_and_replace_variables(nodes)  # Make the variable substitutions
    commands_executed = bashparse.return_nodes_of_type(node, 'command') 
    cds_executed = bashparse.find_specific_command(commands_executed, 'cd', return_as_strings=True)
    for cd_node in cds_executed:
        print(cd_node)
    
Which would return the output:
    
    cd /var
    cd /tmp
    cd /etc
      
## Function Descriptions

- **parse(str):** A wrapper for bashlex.parse. 
    - Takes: a string as an argument 
    - Returns an abstract syntax tree (a bashlex.ast.node object)

- **path_varaible:** an object which holds a path, a node, which can be found at the end of that path, and an optional value field (used in this package when the node is a variable and has a corresponding value). 
    
- **update_variable_list_with_node(node: bashlex.ast.node / list, var_list: dict):** This function finds any variable declarations in the abstract syntax tree(s) and saves the name value pair to the dictionary passed in, such that you can index the dictionary by variable name and return the variable's value. Note, the variables value will always be saved as an array.
    - Takes: node object and variable dictionary
    - Returns: Variable dictionary
- **substitute_variables(node: bashlex.ast.node / list, var_list: dict):** This function identifies all the variables that need replacement in the node(s) passed in. It then references the var_list to identify if a definition for that variable exists. If a definition exists, it will substitute the value. In the event the variable has multiple values (i.e. is an array), multiple nodes corresponding to all the possible replacements will be returned.
    - Takes: node object and variable dictionary
    - Returns: list of nodes
- **add_variable_to_list(var_list: dict, name: str, value: str/array):** Takes the variable list, the name of the variable, and the value(s) to assign. This function adds an index into the variable dict with the value(s) passed into the function. This will add the specified values into the dict index if the value already exists. This just makes sure that all values in the dictionary are arrays. THIS IS NECESSARY FOR THE VARIABLES SECTION OF THE PACKAGE TO WORK
    - Takes: variable dictionary, name of the variable, the value(s) to assign that variable
    - Returns: variable dictionary
- **replace_variables_using_paths(node: bashlex.ast.node / list, paths: list of path_variables, var_list: dict):** This function replaces all the variables in the paths list with their corresponding values in the var_list dictionary. The function then returns an array of all the possible combinations of variable replacements, according to bash's rules. If a varible does not exist in the var_list, then it will not be changed. The ast will have its pos variables changed accordingly and the parameter nodes will be removed if the replacement occurs. 
    - Takes: node object, path_variables to all the variables to replace, and a variable dictionary
    - Returns: list of nodes
- **find_and_replace_variables(nodes: bashlex.ast.node / list, var_list (optional):** This function finds and replaces all the variables in the list. If the list contains variable assignments as well, the var_list will be updated to reflect this and replacements will also include these new values. The function assumes the code is executing in the list's order. So if an assignment happens after the reference, the reference will NOT be given the assigned value.
    - Takes: list of nodes or single node object and optionally a variable dictionary
    - Returns: a list of node objects will all possible variable replacements
    
- **node_level_regex(node: bashlex.ast.node / list, regex:r"str"):** This traverse every node in the ast(s) and checks if part of the word matches the regex. If it does, the matching regex is added to a list, which is returned.        
    - Takes: node and regex to find
    - Returns: list of strings which match the regex

- **find_specific_commands(node: bashlex.ast.node / list, commands_looking_for: list of str, saved_command_dictionary: dict, return_as_strings: bool):** This function checks the ast(s) for exections of commands listed in the commands_looking_for. If the command is found in the ast(s) then its appended to an array as either a command node or the command string. This difference is specified using the return_as_string bool. If an array is passed in, which contains a numnber of asts, the paths will begin with the index into that array.
    - Takes: node object, list of commands to look for (a list of strings), a dictionary to save the commands to, and a bool identifying if the commands should be saved as nodes or strings
    - Returns: the updated command dictionary
- **find_specific_command(node: bashlex.ast.node / list, command: str, return_as_strings: bool):** This function traverses the given node(s) to find any instances of a command being executed. 
    - Takes: node object, command that you're looking for (as a string), and a boolean indicting if you want it to be returned as a string (True) or not (and have the nodes themselves be returned)
- **return_commands_from_variable_delcaraction(node: bashlex.ast.node / list):** This function returns any commands that would be executed in a variable declaration via a command substitution. I.e. a=$(wget www.google.com).
    - Takes: node object
    - Returns: list of nodes
- **return_commands_from_command_substitutions(node: bashlex.ast.node / list):** This function iterates through the ast(s) to find any command substitutions and returns the commands these substitutions would be executing. 
    - Takes: node object
    - Returns: list of nodes
- **return_commands_from_for_loops(node: bashlex.ast.node):** This function looks through node(s) for any for loops and returns all the command nodes in the for loops it finds. 
    - Takes: node object
    - Returns: list of nodes   
- **return_command_aliasing(bashlex.ast.node / list, dict):** This function iterates through all the node provided and notes any time a file gets move from one location to another. If a file is moved, its saved to the dictionary so that you an index by the new file name and recieve the old file name. It saves both the full path and just thee file name
    - Takes: node object and an optional list of command aliases as a dict
    - Returns: An updated list of command aliases as a dict
- **replace_command_aliasing(bashlex.ast.node / list, dict):** This function gathers every command in the nodes provided and if the execute an aliased command which is stored in the command_alias_list dict, then it replaces it with the unaliased command name 
    - Takes: node object and an optional list of command aliases as a dict
    - Returns: a list of node objects with their aliased commands resolved   
- **resolve_command_aliasing(bashlex.ast.node / list, dict):** This function does the job of the above 2 functions in 1 step
    - Takes: node object and an optional list of command aliases as a dict
    - Returns: a list of node objects with their aliased commands resolved 

- **shift_tree_pos(node:bashlex.ast.node / list, shift_amount:int):** This takes node or a list of nodes and the amount to shift all the pos values by. This is used to shift the nodes pos by any given value, instead of its offset in the string. Returns the node with the updated pos values 
    - Takes: node object and the shift amount (int) 
    - Returns: the shifted node object
- **shift_tree_pos_to_start(node: bashlex.ast.node / list):** If a single node is provided it shifts the given node's pos to starting at 0. If an array of nodes are given, the first node's pos starts at zero and all following nodes have pos values that follow the node preceding it. A helpful wrapper of the above function. Returns the newly shifted node
    - Takes: node object
    - Returns: the shifted node object
- **return_variable_paths(node: bashlex.ast.node / list):** This function is a helpful wrapper to the above function. Should be used to find all the varaibles used in the node. Returns a list of the path_variables which can be used to identify all the variables in the node. If a list of paths is given to the function, the path indexes will being with the index into the array
    - Takes: node object
    - Returns: list of path variables to the variables
- **return_paths_to_node_type(node:bashlex.ast.node / list, node_type: str):** This function iterates through the given ast to find the location of all the nodes which are of kind node_type. It then returns a list of path_variables which can be used to identify and traverse to the given nodes. current_path and paths should be empty on initial call. If a list of paths is given to the function, the path indexes will being with the index into the array 
    - Takes: node object and the node kind one is looking for (str)
    - Returns: list of path variables to the corresponding nodes
- **return_nodes_of_type(node: bashlex.ast.node / list, node_type: str):** This function takes a node and a string of the node type one is looking for. This returns the nodes themselves, as opposed to path_variables.
    - Takes: node object and string indicating type looking for
    - Returns: list of node objects
- **convert_tree_to_string(node: bashlex.ast.node):** This function converts the given ast back into a readable string. It will not exactly maintain the formatting (as \n is dropped in parsing) but it is correct and readable nonetheless.
    - Takes: node object
    - Returns: string
- **return_node_at_path(bashlex.ast.node, path_variable or list of ints):** This function naivgates the ast down the path specified in the path argument. It then returns the actual node at that location, rather than a copy as is the case with a lot of other functions in this package.
