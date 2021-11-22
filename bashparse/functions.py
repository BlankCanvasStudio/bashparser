from bashparse.ast import return_nodes_of_type, return_node_at_path, return_paths_to_node_type, return_variable_paths, shift_ast_pos_to_start, shift_ast_pos
from bashparse.variables import substitute_variables, replace_variables_using_paths
import bashparse, copy, enum


def build_function_dictionary(nodes, function_dictionary={}):
	if type(nodes) is not list: nodes = [nodes]
	for node in nodes:
		if type(node) is not bashparse.node: raise ValueError('nodes must be made up of bashparse.node elements')

	functions = return_nodes_of_type(nodes, 'function')
	functions = functions + functions
	for function in functions:
		function_body = None
		compound_nodes = return_nodes_of_type(function, 'compound')

		for compound_node in compound_nodes:
			if compound_node.list[0].kind == 'reservedword' and compound_node.list[0].word == '{':
				function_body = copy.deepcopy(compound_node)
				function_body.list = function_body.list[1:-1]
				break
		if function_body is not None:
			function_dictionary[function.parts[0].word] = function_body

	return function_dictionary

def replace_functions(nodes, function_dictionary={}):
	if type(nodes) is not list: nodes = [nodes]
	for node in nodes:
		if type(node) is not bashparse.node: raise ValueError('nodes must be made up of bashparse.node elements')
	if type(function_dictionary) is not dict: raise ValueError('function_dictionary must be a dictionary')

	for node in nodes:
		commands = return_paths_to_node_type(node, 'command')
		for command in commands:
			if len(command.node.parts) and command.node.parts[0].word in function_dictionary:
				command_node = return_node_at_path(node, command.path)
				arguments = command_node.parts[1:]
				argument_var_list = {}
				for i, argument in enumerate(arguments): 
					argument_var_list[str(i+1)] = [ argument.word ]
				function_body = function_dictionary[command.node.parts[0].word]
				function_body = replace_function_arguments(function_body, argument_var_list)[0]
				command_node.kind = 'compound'
				setattr(command_node, 'list', function_body.list)
				setattr(command_node, 'redirects', function_body.redirects)
				delattr(command_node, 'parts')
	return nodes


def replace_function_arguments(nodes, argument_var_list={}):
	if type(nodes) is not list: nodes = [nodes]
	for node in nodes:
		if type(node) is not bashparse.node: raise ValueError('nodes must be made up of bashparse.node elements')
	if type(argument_var_list) is not dict: raise ValueError('function_dictionary must be a dictionary')
	replaced_nodes = []
	for node in nodes:
		replaced_node = node
		variables = return_variable_paths(node)
		for variable in reversed(variables):
			if variable.node.value in argument_var_list:
				variable.path = variable.path[1:]
				replaced_node = replace_variables_using_paths(node, variable, argument_var_list)[0]
				variable.path = variable.path[:-1]
				node_one_up = return_node_at_path(replaced_node, variable)
				node_one_up.parts = bashparse.parse('"'+node_one_up.word+'"')[0].parts[0].parts
				node_one_up.parts = shift_ast_pos(shift_ast_pos_to_start(node_one_up.parts), node_one_up.pos[0])
		replaced_nodes += [ replaced_node ]
	return replaced_nodes