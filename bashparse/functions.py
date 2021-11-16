from bashparse.ast import return_nodes_of_type, return_node_at_path, return_paths_to_node_type
import bashparse, copy


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
	
	for node in nodes:
		commands = return_paths_to_node_type(node, 'command')
		for command in commands:
			if len(command.node.parts) and command.node.parts[0].word in function_dictionary:
				command_node = return_node_at_path(node, command.path[:-1])
				function_body = function_dictionary[command.node.parts[0].word]
				command_node.kind = 'compound'
				setattr(command_node, 'list', function_body.list)
				setattr(command_node, 'redirects', function_body.redirects)
				delattr(command_node, 'parts')
	return nodes
