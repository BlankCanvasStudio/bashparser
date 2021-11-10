"""Describe module and how to use it here..."""

from bashparse import variables, commands, regex
import bashlex

parse = bashlex.parse

return_variable_paths = variables.return_variable_paths  
replace_variables = variables.replace_variables  
	# (node, paths to variables to replace, variable dict)  Swaps the variables in 2nd arg with their values and fixes ast accordingly
	# returns an array of nodes, which make up all the possible options for all variable replacementss
update_variable_list = variables.update_variable_list  
	# (node, variable dict) strips any variables out of ast and saves them to variable list. Also saves mv x y for later use (could be separated)
	# returns an updated variable dict
substitute_variables = variables.substitute_variables  
	# (node, variable list)  runs the whole gambit of finding all the variable locations, swapping them, and adjusting ast
	# returns an array of nodes which are all permutations of variable replacements possible within bash rules
add_variables_to_var_list = variables.add_var_to_var_list
	# (variable dict, name, value) Adds the corresponding name and value to dictionary. Planning on people misuing the dictionary
	# returns the updated variable dict
return_paths_to_node_type = variables.return_paths_to_node_type
	# (node, [], [], node type looking for) Finds all the paths to nodes in ast which are of a certain kind. 
	# returns a list of path_variables to those nodes
	# if you pass node type='parameter', it will find all the variables. the above find all variables is just convenient wrapper of this function
shift_tree_pos = variables.shift_tree_pos
	# The pos variable identifies where in the parsed string a particular value is. if the string gets longer we need to adjust it (ie var repalcement)
	# shifts all the positions in an ast by a given value. Only useful if ast before this one gets x longer or shorter (happens on variable repalcement)
	# super nice use but necessary if you want to do massive work with the framework. 
	# returns the shifted tree (ie a bashlex.ast.node)
shift_tree_pos_to_start = variables.shift_tree_pos_to_start
	# shifts the pos variable so that it starts a 0. just a userful wrapper of the above class


node_level_regex = regex.node_level_regex
	# (node, regex string). This will find all occurances of a regex in a given node of the ast
	# Could expand this to regex multiple nodes of ast but that's not really useful as of now and ast intepretation
	# would achieve the same, if not a better result


find_specific_commands = commands.find_specific_commands
	# (node, list of commands you're looking for, dict to save commands into, bool if the nodes should be saved as strings (and not ast nodes))
	# This looks for given commands in an ast node. if it is a command then it gets saved to the dict
	# Returns the updated command dictionary
return_commands_from_variable_delcaraction = commands.return_commands_from_variable_delcaraction
	# (node) strips the commands from a variable declaration if its of the form a=$(some command)\
	# returns a list of any commands found in the node
