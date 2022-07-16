from bashparse import variables, commands, ast, functions, template, main, chunk, unroll
import bashlex

parse = bashlex.parse

node = bashlex.ast.node

NodeVisitor = ast.NodeVisitor

# path_variable = path_variable.path_variable


update_variable_list_with_node = variables.update_variable_list_with_node  

substitute_variables = variables.substitute_variables  
	
add_variable_to_list = variables.add_variable_to_list
	
replace_variables = variables.replace_variables  

# find_and_replace_variables = variables.find_and_replace_variables     # replaced with substitute variables


# node_level_regex = regex.node_level_regex


#find_specific_commands = commands.find_specific_commands

#find_specific_command = commands.find_specific_command
	
# return_commands_from_variable_delcaraction = commands.return_commands_from_variable_delcaraction

# return_commands_from_command_substitutions = commands.return_commands_from_command_substitutions

# return_commands_from_for_loops = commands.return_commands_from_for_loops

return_command_aliasing = commands.return_command_aliasing

replace_command_aliasing = commands.replace_command_aliasing

resolve_command_aliasing = commands.resolve_command_aliasing


#shift_tree_pos = ast.shift_ast_pos
	
#shift_tree_pos_to_start = ast.shift_ast_pos_to_start

#return_variable_paths = ast.return_variable_paths

# return_paths_to_node_type = ast.return_paths_to_node_type

# return_nodes_of_type = ast.return_nodes_of_type

# convert_tree_to_string = ast.convert_tree_to_string

# return_node_at_path = ast.return_node_at_path


# build_function_dictionary = functions.build_function_dictionary

replace_functions = functions.replace_functions



# Bashtemplate 

Chunk = chunk.Chunk

Template = template.Template
# The object class

generate_templates = main.generate_templates
    # Takes an array of nodes

generate_useful_templates = main.find_useful_templates

templatize = \
    main.templatize

filter_templates = \
    main.filter_templates



# bashunroll

basic_unroll = unroll.basic_node_unroll
replacement_unroll = unroll.replacement_based_unroll