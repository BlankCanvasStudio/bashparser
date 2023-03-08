#!/bin/python3
from bashparser.variables import replace_variables
from bashparser.ast import NodeVisitor, shift_ast_right_of_path, expand_ast_along_path
from bashparser.ast import CONT, DONT_DESCEND
import bashparser.ast as bpast
import copy, bashlex


def build_fn_table(nodes, fn_dict={}):
	""" Iterates over the node looking for any function definitions. If one is found its added to the function 
		dictionary with index of funciton name and a value of the list node present in between the brackets.
		This allows for eaier argument replacement later (pass in list node rather than array of commands).
		Returns the function dictionary for good measure but acts BY REFERENCE """
	if type(nodes) is not list: nodes = [ nodes ]
	for node in nodes:
		if type(node) is not bashlex.ast.node: raise ValueError('Error! bashparser.functions.build_fn_table(node != bashlex.ast.node)')
	if type(fn_dict) is not dict: raise ValueError('Error! bashparser.functions.build_fn_table(fn_dict != dict)')

	def apply_fn(node, vstr, fn_dict):
		if node.kind != 'function': return CONT
		compound_node = node.parts[-1]		# The last node is the body of the function

		if compound_node.list[0].kind != 'reservedword' and compound_node.list[0].word != '{': return CONT
		
		function_body = copy.deepcopy(compound_node)
		function_body.list = function_body.list[1:-1]				# Brackets are 1st & last elements
		fn_cmds = copy.deepcopy(compound_node).list[1:-1][0]		# Brackets are 1st & last elements. The center element is a list node containing all the commands to be executed
		fn_cmds = NodeVisitor(fn_cmds).justify()
		fn_dict[node.parts[0].word] = fn_cmds					# node.parts[0] is the function's name				
	for node in nodes:
		vstr = NodeVisitor(node)
		vstr.apply(apply_fn, vstr, fn_dict)
	return fn_dict


def resolve_functions(nodes, fn_dict, var_list = None):
	if type(nodes) is not list: nodes = [ nodes ]
	for node in nodes:
		if type(node) is not bashlex.ast.node: raise ValueError('Error! bashparser.resolve_functions.build_fn_table(node != bashlex.ast.node)')
	if type(fn_dict) is not dict: raise ValueError('Error! bashparser.resolve_functions.build_fn_table(fn_dict != dict)')
	if var_list is not None and type(var_list) is not dict: raise ValueError('Error! bashparser.functions.resolve_functions(var_list != dict)')
	
	def build_body_replacements(node, vstr, fn_dict, fn_repl_dict, var_list = None):
		""" Finds all the function calls in node, takes in the arguments, replaces all
			arguments in the function body, and saves the pathation where it should 
			be replaced in the funct. Function replacement needs to happen at the end 
			because we need to expand the trees, so self._root can no longer be used to 
			navigate. Operates BY REFERENCE """
		if node.kind != 'command': return CONT
		if not (len(node.parts) and hasattr(node.parts[0], 'word') \
					and node.parts[0].word in fn_dict): return CONT

		# Get the arguments from the function call
		arguments = node.parts[1:]
		arg_list = {}

		""" We replace the arguments with the nodes themselves. This allows for the function arguments 
			to contain parameters themselves and still be replaced properly """
		for i, argument in enumerate(arguments): 
			arg_list[str(i+1)] = [ argument ]
		# Get the non-replaced function body
		
		function_body = fn_dict[node.parts[0].word]		# fn_repl_dict is indexed by a string encoded path to the node to replace
		
		# Replace the arguments in the function body and save result to fn_replace_dict
		bodies_replaced = replace_variables(function_body, arg_list)
		fn_repl_dict[' '.join([str(x) for x in vstr.path])] = bodies_replaced		# encode path as string cause lists are unhashable

		return CONT					# Investigate nested function calls and see if we can put DONT_DESCEND here

	def replace_bodies(node, vstr, fn_repl_dict):
		""" Run after the nodes have been iterated over to build function bodies. This replaces
			all the functions specified in the keys of fn_repl_dict with the commands present in the 
			list node of the key's corresponding value. Allows for multiple function bodies to replace 
			a single function call. Useful for analysis. """

		for path, bodies in reversed(fn_repl_dict.items()):	# We need to iterate this backwards so the index doesn't change 
			if len(path):
				path = [int(x) for x in path.split(' ')]			# lists are unhashable so we converted it to a space separated string
			else:
				path = []											# pops an error without this if	
			# Support for multiple function body replacement (ie control flow divergence on the function itself)
			# Not completely sure its necessary but will be helpful for scripting analysis
			new_nodes = []
			for body in bodies: new_nodes = copy.deepcopy(vstr.nodes) 
			vstr.nodes = new_nodes

			""" Need to chop the array of nodes into sections where each section (which is 1 division_width wide)
				contains a unique value for that function body. This way all function values are replace together, 
				ie section 1 is replaced only with the 1st value of the function. Think value of x for x in [1, 2, 3] """
			division_width = len(vstr.nodes) // len(bodies)
			for i, body in enumerate(bodies):
				for j in range(i*division_width, (i+1)*division_width):
					if not len(path):		# if there is no path then nodes[j] is the node getting repalced
						vstr.nodes[j] = NodeVisitor(body).justify()
						continue

					delta = 0													# Amount we need to shift the tree after repalcement

					parent = vstr.at_path(vstr.nodes[j], path[:-1])
					new_children = NodeVisitor(parent).children()[:path[-1]] 	# children for the parent up to the function replacement is the same

					# Find the start index of the node with the end of the last child+1 or the start of the parent if its the first child
					if len(new_children):
						start = new_children[-1].pos[1] + 1						# Find the pos[0] of the nodes being injected 
					else:
						start = parent.pos[0]
					body = NodeVisitor(body).align(delta=start)					# bodies are justified in build_fn_table. Now aligned them to correct start

					while body.parts[-1].kind == 'operator': 					# parser automatically removes extra '\n', ';', etc so we must as well. list probably ends with one (who starts next line after function inline?)
						body.parts = body.parts[:-1]
					new_children += body.parts									# Add the new body elements to the new_children list (remember the body is a list node of commands for ease of programming)

					# Align and add all the children after the function call. Other than alignment, there is no change to these nodes
					end_of_original_children = NodeVisitor(parent).children()[path[-1]+1:]
					delta += -end_of_original_children[-1].pos[1]
					for new_child in end_of_original_children:
						start = new_children[-1].pos[1] + 1
						new_child = NodeVisitor(new_child).justify()
						new_child = NodeVisitor(new_child).align(delta=start) 
						new_children += [ new_child ]
					delta += new_children[-1].pos[1] 							# Delta = new_children.pos[1] - old_children.pos[0]

					# Align nodes on & following path to last child node. Accounts for width of cmds injected (kinda like variable replacement)
					vstr.set_children(parent, new_children)
					vstr.nodes[j] = expand_ast_along_path(vstr.nodes[j], path[:-1], delta)
					path_to_shift_right_of = path[:-1] + [ len(new_children) ]
					vstr.nodes[j] = shift_ast_right_of_path(vstr.nodes[j], path_to_shift_right_of, delta)

		return vstr.nodes

	to_return = []
	for node in nodes:
		fn_repl_dict = {}
		vstr = NodeVisitor(node)
		vstr.apply(build_body_replacements, vstr, fn_dict, fn_repl_dict)
		to_return += replace_bodies(node, vstr, fn_repl_dict)
	return to_return


def build_and_resolve_fns(nodes, fn_dict = {}, var_list = None):
	""" Helpful wrapper """
	if type(nodes) is not list: nodes = [ nodes ]
	for node in nodes:
		if type(node) is not bashlex.ast.node: raise ValueError('Error! bashparser.resolve_functions.build_and_resolve_fns(node != bashlex.ast.node)')
	if type(fn_dict) is not dict: raise ValueError('Error! bashparser.resolve_functions.build_and_resolve_fns(fn_dict != dict)')
	if var_list is not None and type(var_list) is not dict: raise ValueError('Error! bashparser.functions.build_and_resolve_fns(var_list != dict)')
	
	new_nodes = []
	for node in nodes: 
		fn_dict = build_fn_table(node, fn_dict)
		new_nodes += resolve_functions(node, fn_dict, var_list)
	return new_nodes
	