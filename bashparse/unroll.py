import bashparse

def basic_node_unroll(nodes, function_dict = {}, command_alias_list={}):
	# Command substitutions are gonna be weird
	if type(nodes) is not list: nodes = [nodes]
	for node in nodes: 
		if type(node) is not bashparse.node: raise ValueError('nodes must be of type bashparse.node')
	unrolled_nodes = []

	for node in nodes: 
		if node.kind == 'compound':
			unrolled_nodes += basic_node_unroll(node.list, function_dict, command_alias_list)
		elif node.kind == 'for':
			if len(node.parts) > 4:
				unrolled_nodes += basic_node_unroll(node.parts[4:])
				# command_nodes = bashparse.return_paths_to_node_type(node.parts[4:], 'command')
				# for command in command_nodes:
				# 	unrolled_nodes += basic_node_unroll(command.node, function_dict, command_alias_list)
		elif node.kind == 'if':
			unrolled_nodes += [ node ]
		elif node.kind == 'command':
			command_alias_list = bashparse.return_command_aliasing(node, command_alias_list)
			node = bashparse.replace_command_aliasing(node, command_alias_list)
			node = bashparse.replace_functions(node, function_dict)
			for itr in node:
				if itr.kind == 'compound': # ie function replacement happened
					unrolled_nodes += basic_node_unroll(itr.list, function_dict, command_alias_list)
				else:
					unrolled_nodes += [ itr ]
		elif node.kind == 'function':
			function_dict = bashparse.build_function_dictionary(node, function_dict)
		elif hasattr(node, 'parts'):
			if node.kind == 'pipeline':
			# Pipelined nodes shoud stay together
				for i, part in enumerate(node.parts):
					if part.kind != 'pipe': node.parts[i] = basic_node_unroll(part)[0]
				unrolled_nodes+= [ node ]
			else:
				unrolled_nodes += basic_node_unroll(node.parts)
		elif hasattr(node, 'list'):
			unrolled_nodes += basic_node_unroll(node.list)
	return unrolled_nodes


def replacement_based_unroll(nodes, var_list={}):
	# The ordering of this function is important. Tread lightly
	var_list += bashparse.update_variable_list_with_node(nodes, var_list)
	replaced_nodes = bashparse.substitute_variables(nodes, var_list)
	
	function_dict = bashparse.build_function_dictionary(replaced_nodes)
	replaced_nodes = bashparse.replace_functions(replaced_nodes, function_dict)
	
	unrolled_nodes = basic_node_unroll(replaced_nodes)
	
	return unrolled_nodes

