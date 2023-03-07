import bashparse, bashlex
from bashparse.ast import NodeVisitor


def strip_cmd(nodes):
	if type(nodes) is not list: nodes = [nodes]
	for node in nodes: 
		if type(node) is not bashlex.ast.node: raise ValueError('Error! bashparse.unroll.basic_unroll(nodes != list of bashlex.ast.nodes)')
	
	def apply_fn(node, vstr):
		if node.kind == 'command': 
			vstr.nodes += [node]
			return bashparse.DONT_DESCEND
		if node.kind == 'pipeline':
			vstr.nodes += [node]
			return bashparse.DONT_DESCEND
		if node.kind == 'if':
			vstr.nodes += [node]
			return bashparse.DONT_DESCEND
		if node.kind == 'function':
			vstr.nodes += [node]
			return bashparse.DONT_DESCEND
		return bashparse.CONT

	unrolled_commands = []
	for node in nodes:
		vstr = NodeVisitor(node)
		vstr.nodes = []
		vstr.apply(apply_fn, vstr)
		unrolled_commands += vstr.nodes
	return unrolled_commands


def advanced_unroll(nodes, var_list={}, fn_dict={}, alias_table={}):
	# The ordering of this function is important. Tread lightly

	nodes = bashparse.build_and_resolve_aliasing(nodes, alias_table)

	nodes = bashparse.build_and_resolve_fns(nodes, fn_dict)

	nodes = bashparse.substitute_variables(nodes, var_list)

	commands = strip_cmd(nodes)

	return commands
