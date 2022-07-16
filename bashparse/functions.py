# from bashparse.ast import return_variable_paths, shift_ast_pos_to_start, shift_ast_pos, return_node_at_path,  return_nodes_of_type, return_paths_to_node_type, 
from bashparse.variables import substitute_variables, replace_variables
from bashparse.ast import NodeVisitor, CONT
import bashparse.ast as bpast
import bashparse, copy, enum


def replace_functions(nodes, fn_dict):

	def apply_fn(node, vstr, fn_dict, fn_repl_dict):
		if node.kind == 'function':		
			compound_node = node.parts[-1]		# The last node is the body of the function

			if compound_node.list[0].kind == 'reservedword' and compound_node.list[0].word == '{':
				function_body = copy.deepcopy(compound_node)
				function_body.list = function_body.list[1:-1]				# Brackets are 1st & last elements
				fn_cmds = copy.deepcopy(compound_node).list[1:-1][0]		# Brackets are 1st & last elements. The center element is a list node containing all the commands to be executed
				fn_cmds = NodeVisitor(fn_cmds).justify()
				fn_dict[node.parts[0].word] = fn_cmds					# node.parts[0] is the function's name	

		elif node.kind == 'command':

				if not (len(node.parts) and hasattr(node.parts[0], 'word') \
					and node.parts[0].word in fn_dict): return CONT

				arguments = node.parts[1:]
				arg_list = {}
				for i, argument in enumerate(arguments): 
					arg_list[str(i+1)] = [ argument.word ]
				function_body = fn_dict[node.parts[0].word]
				bodies_replaced = replace_variables(function_body, arg_list)
				fn_repl_dict[' '.join([str(x) for x in vstr.path])] = bodies_replaced		# encode path as string cause lists are unhashable

		return CONT

	def do_replacement(node, vstr, fn_repl_dict):
		for loc, bodies in reversed(fn_repl_dict.items()):	# We need to iterate this backwards so the index doesn't change 
			loc = [int(x) for x in loc.split(' ')]			# lists are unhashable so we converted it to a space separated string
			new_nodes = []
			for body in bodies: new_nodes = copy.deepcopy(vstr.nodes) 
			vstr.nodes = new_nodes

			division_width = len(vstr.nodes) // len(bodies)
			for i, body in enumerate(bodies):
				for j in range(i*division_width, (i+1)*division_width):
					parent = vstr.at_path(vstr.nodes[j], loc[:-1])
					new_children = NodeVisitor(parent).children()[:loc[-1]] 
					start = new_children[-1].pos[1] + 1

					body = NodeVisitor(body).align(delta=start)

					while body.parts[-1].kind == 'operator' and body.parts[-1].op == '\n':		# parser automatically removes extra \n so we must as well
						body.parts = body.parts[:-1]
					new_children += body.parts
					
					index_of_last_new_child = len(new_children)
					
					end_of_original_children = NodeVisitor(parent).children()[loc[-1]+1:]
					delta = -end_of_original_children[-1].pos[1]
					for new_child in end_of_original_children:
						start = new_children[-1].pos[1] + 1
						new_child = NodeVisitor(new_child).justify()
						new_child = NodeVisitor(new_child).align(delta=start) 
						new_children += [ new_child ]

					delta += new_children[-1].pos[1] 
					vstr.set_children(parent, new_children)
					""" Need to expand along path & right of path to account for new children """
					vstr.nodes[j] = bpast.expand_ast_along_path(vstr.nodes[j], loc[:-1], delta)
					path_to_shift_right_of = loc[:-1] + [ index_of_last_new_child ]
					vstr.nodes[j] = bpast.shift_ast_right_of_path(vstr.nodes[j], path_to_shift_right_of, delta)

		return vstr.nodes

	replaced_nodes = []
	fn_repl_dict = {}
	for node in nodes:
		vstr = NodeVisitor(node)
		vstr.apply(apply_fn, vstr, fn_dict, fn_repl_dict)
		replaced_nodes += do_replacement(node, vstr, fn_repl_dict) 
	return replaced_nodes
