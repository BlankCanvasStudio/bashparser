#!/bin/python3
import bashparser, bashlex
from bashparser.ast import NodeVisitor


def strip_cmd(nodes):
	if type(nodes) is not list: nodes = [nodes]
	for node in nodes: 
		if type(node) is not bashlex.ast.node: raise ValueError('Error! bashparser.unroll.basic_unroll(nodes != list of bashlex.ast.nodes)')
	
	def apply_fn(node, vstr):
		if node.kind == 'command': 
			vstr.nodes += [node]
			return bashparser.DONT_DESCEND
		if node.kind == 'pipeline':
			vstr.nodes += [node]
			return bashparser.DONT_DESCEND
		if node.kind == 'if':
			vstr.nodes += [node]
			return bashparser.DONT_DESCEND
		if node.kind == 'function':
			vstr.nodes += [node]
			return bashparser.DONT_DESCEND
		return bashparser.CONT

	unrolled_commands = []
	for node in nodes:
		vstr = NodeVisitor(node)
		vstr.nodes = []
		vstr.apply(apply_fn, vstr)
		unrolled_commands += vstr.nodes
	return unrolled_commands


def advanced_unroll(nodes, var_list={}, fn_dict={}, alias_table={}, strip_cmds=True):
	# The ordering of this function is important. Tread lightly

	nodes = bashparser.build_and_resolve_aliasing(nodes, alias_table)

	nodes = bashparser.build_and_resolve_fns(nodes, fn_dict)

	nodes = bashparser.substitute_variables(nodes, var_list)

	if strip_cmds:
		ret_val = strip_cmd(nodes)
	else:
		ret_val = nodes

	return ret_val


def main():
	import argparse

	parser = argparse.ArgumentParser()
	parser.add_argument("--cmds", help='Strip the commands from the bash file', action='store_true')
	parser.add_argument("--file", help="The filename of the bash script you'd like to unroll", type=str)
	args = parser.parse_args()


	if args.file is None:
		print("Please specify a filename with --file")
	
	else:
		if args.cmds:
			nodes = bashparser.parse(open(args.file).read())
			res = strip_cmd(nodes)
			for node in res:
				print(str(bashparser.NodeVisitor(node)))
		else:
			nodes = bashparser.parse(open(args.file).read())
			res = advanced_unroll(nodes)
			for node in res:
				print(str(bashparser.NodeVisitor(node)))

if __name__ == "__main__":
	main()
