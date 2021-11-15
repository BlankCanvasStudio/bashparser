from bashparse import variables, commands, regex, ast, path_variable
import bashlex

parse = bashlex.parse

node = bashlex.ast.node


path_variable = path_variable.path_variable


update_variable_list_with_node = variables.update_variable_list_with_node  

substitute_variables = variables.substitute_variables  
	
add_variable_to_list = variables.add_variable_to_list
	
replace_variables_using_paths = variables.replace_variables_using_paths  

find_and_replace_variables = variables.find_and_replace_variables


node_level_regex = regex.node_level_regex


find_specific_commands = commands.find_specific_commands

find_specific_command = commands.find_specific_command
	
return_commands_from_variable_delcaraction = commands.return_commands_from_variable_delcaraction

return_commands_from_command_substitutions = commands.return_commands_from_command_substitutions

return_commands_from_for_loops = commands.return_commands_from_for_loops

return_command_aliasing = commands.return_command_aliasing

replace_command_aliasing = commands.replace_command_aliasing

resolve_command_aliasing = commands.resolve_command_aliasing


shift_tree_pos = ast.shift_ast_pos
	
shift_tree_pos_to_start = ast.shift_ast_pos_to_start

return_variable_paths = ast.return_variable_paths

return_paths_to_node_type = ast.return_paths_to_node_type

return_nodes_of_type = ast.return_nodes_of_type

convert_tree_to_string = ast.convert_tree_to_string

return_node_at_path = ast.return_node_at_path