from bashparse import variables, commands, regex, ast, path_variable
import bashlex

parse = bashlex.parse


path_variable = path_variable.path_variable


update_variable_list = variables.update_variable_list  

substitute_variables = variables.substitute_variables  
	
add_variables_to_var_list = variables.add_var_to_var_list
	
replace_variables = variables.replace_variables  


node_level_regex = regex.node_level_regex


find_specific_commands = commands.find_specific_commands
	
return_commands_from_variable_delcaraction = commands.return_commands_from_variable_delcaraction

return_commands_from_command_substitutions = commands.return_commands_from_command_substitutions # Add doc & test


shift_tree_pos = ast.shift_ast_pos
	
shift_tree_pos_to_start = ast.shift_ast_pos_to_start

return_variable_paths = ast.return_variable_paths

return_paths_to_node_type = ast.return_paths_to_node_type

convert_tree_to_string = ast.convert_tree_to_string # Add doc & test