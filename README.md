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
        commands_executed = []
        for node in replaced_nodes:  # Get all the command nodes from the replaced code
            commands_executed += bashparse.return_nodes_of_type(node, 'command')  
            # Get all the commands executed from newly replaced nodes
        for command in commands_executed:  # Print the command nodes as string
            print(bashparse.convert_tree_to_string(command))
            # print the found commands as string
    
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
        commands_executed = []
        cds_executed = []
        for node in replaced_nodes:  # Get all the command nodes from the replaced code
                commands_executed += bashparse.return_nodes_of_type(node, 'command')  
                # Get all the commands executed from newly replaced nodes
        for command in commands_executed:  # Print the command nodes as string
                cds_executed += bashparse.find_specific_command(command, 'cd', True)
                cds_executed = list(set(cds_executed))
        for cd_node in cds_executed:
                print(cd_node)
    
    Which would return the output:
    
        cd /var
        cd /tmp
        cd /etc
    
    
## Function Descriptions

- parse(str): A wrapper for bashlex.parse. 
    - Takes: a string as an argument 
    - Returns an abstract syntax tree (a bashlex.ast.node object)

- path_varaible: an object which holds a path, a node, which can be found at the end of that path, and an optional value field (used in this package when the node is a variable and has a corresponding value). 
    
- update_variable_list_with_node(node: bashlex.ast.node, var_list: dict): This function finds any variable declarations in the abstract syntax tree and saves the name value pair to the dictionary passed in, such that you can index the dictionary by variable name and return the variable's value. Note, the variables value will always be saved as an array.
    - Takes: node object and variable dictionary
    - Returns: Variable dictionary
- substitute_variables(node: bashlex.ast.node, var_list: dict): This function identifies all the variables that need replacement in the node passed in. It then references the var_list to identify if a definition for that variable exists. If a definition exists, it will substitute the value. In the event the variable has multiple values (i.e. is an array), multiple nodes corresponding to all the possible replacements will be returned.
    - Takes: node object and variable dictionary
    - Returns: list of nodes
- add_variable_to_list(var_list: dict, name: str, value: str/array): Takes the variable list, the name of the variable, and the value(s) to assign. This function adds an index into the variable dict with the value(s) passed into the function. This will add the specified values into the dict index if the value already exists. This just makes sure that all values in the dictionary are arrays. THIS IS NECESSARY FOR THE VARIABLES SECTION OF THE PACKAGE TO WORK
    - Takes: variable dictionary, name of the variable, the value(s) to assign that variable
    - Returns: variable dictionary
- replace_variables_using_paths(node: bashlex.ast.node, paths: list of path_variables, var_list: dict): This function replaces all the variables in the paths list with their corresponding values in the var_list dictionary. The function then returns an array of all the possible combinations of variable replacements, according to bash's rules. If a varible does not exist in the var_list, then it will not be changed. The ast will have its pos variables changed accordingly and the parameter nodes will be removed if the replacement occurs. 
    - Takes: node object, path_variables to all the variables to replace, and a variable dictionary
    - Returns: list of nodes
- find_and_replace_variables(nodes: list/bashlex.ast.node, var_list (optional): This function finds and replaces all the variables in the list. If the list contains variable assignments as well, the var_list will be updated to reflect this and replacements will also include these new values. The function assumes the code is executing in the list's order. So if an assignment happens after the reference, the reference will NOT be given the assigned value.
    - Takes: list of nodes or single node object and optionally a variable dictionary
    - Returns: a list of node objects will all possible variable replacements
    
- node_level_regex(node: bashlex.ast.node, regex:r"str"): This traverse every node in the ast and checks if part of the word matches the regex. If it does, the matching regex is added to a list, which is returned.        
    - Takes: node and regex to find
    - Returns: list of strings which match the regex

- find_specific_commands(node: bashlex.ast.node, commands_looking_for: list of str, saved_command_dictionary: dict, return_as_string: bool): This function checks the ast for exections of commands listed in the commands_looking_for. If the command is found in the ast then its appended to an array as either a command node or the command string. This difference is specified using the return_as_string bool.
    - Takes: node object, list of commands to look for (a list of strings), a dictionary to save the commands to, and a bool identifying if the commands should be saved as nodes or strings
    - Returns: the updated command dictionary
- return_commands_from_variable_delcaraction(node: bashlex.ast.node): This function returns any commands that would be executed in a variable declaration via a command substitution. I.e. a=$(wget www.google.com).
    - Takes: node object
    - Returns: list of nodes
- return_commands_from_command_substitutions(node: bashlex.ast.node): This function iterates through the ast to find any command substitutions and returns the commands these substitutions would be executing. 
    - Takes: node object
    - Returns: list of nodes

- shift_tree_pos(node:bashlex.ast.node, shift_amount:int): This takes a node and the amount to shift all the pos values by. This is used to shift a nodes to start at any given value, instead of its offset in the string. Returns the node with the updated pos values 
    - Takes: node object and the shift amount (int) 
    - Returns: the shifted node object
- shift_tree_pos_to_start(node: bashlex.ast.node): Shifts a given node pos to starting at 0. A helpful wrapper of the above function. Returns the newly shifted node
    - Takes: node object
    - Returns: the shifted node object
- return_paths_to_node_type(node:bashlex.ast.node, node_type: str): This function iterates through the given ast to find the location of all the nodes which are of kind node_type. It then returns a list of path_variables which can be used to identify and traverse to the given nodes. current_path and paths should be empty on initial call 
    - Takes: node object and the node kind one is looking for (str)
    - Returns: list of path variables to the corresponding nodes
- return_variable_paths(node: bashlex.ast.node): This function is a helpful wrapper to the above function. Should be used to find all the varaibles used in the node. Returns a list of the path_variables which can be used to identify all the variables in the node.
    - Takes: node object
    - Returns: list of path variables to the variables
- convert_tree_to_string(node: bashlex.ast.node): This function converts the given ast back into a readable string. It will not exactly maintain the formatting (as \n is dropped in parsing) but it is correct and readable nonetheless.
    - Takes: node object
    - Returns: string
