""" This file is just going to test featuers that work in between files 
Basically just dedicated to edge cases that breaks the code. 
I need to make sure every new update keeps the important featuers"""

from unittest import TestCase
import bashparse
import bashparse.variables as bpvar
from bashparse import NodeVisitor
# from bashparse.ast import justify

import os

class TestFeatures(TestCase):

	def test_scoping_unrolling_and_functions(self):
		#print()
		#print(open('./bashparse/test/features_test_code.txt').readlines()[4])
		#print(bashparse.parse(open('./bashparse/test/features_test_code.txt').readlines()[1]))
		expected_results = bashparse.parse('yep() { \n echo global vars: $i $j\n echo functional vars: $1\n }') \
							+ bashparse.parse('for i in 1 2; do \n for j in a b; do\n echo 1 a foo\n echo global vars: 1 a\n echo functional vars: "1 .. a" \n done\n done ') \
							+ bashparse.parse('for i in 1 2; do \n for j in a b; do\n echo 1 b foo\n echo global vars: 1 b\n echo functional vars: "1 .. b" \n done\n done ') \
							+ bashparse.parse('for i in 1 2; do \n for j in a b; do\n echo 2 a foo\n echo global vars: 2 a\n echo functional vars: "2 .. a" \n done\n done ') \
							+ bashparse.parse('for i in 1 2; do \n for j in a b; do\n echo 2 b foo\n echo global vars: 2 b\n echo functional vars: "2 .. b" \n done\n done ')
		# bashparse.parse(''.join(open('./bashparse/test/features_test_code.txt').readlines()[4:9]))
		for i, result in enumerate(expected_results):
			expected_results[i] = NodeVisitor(expected_results[i]).justify()
		# expected_results = expected_results[1:]
		#nodes = bashparse.parse(''.join(open('./bashparse/test/features_test_code.txt').readlines()[1])) \
		#		+ bashparse.parse(''.join(open('./bashparse/test/features_test_code.txt').readlines()[2])) \
		#		+ bashparse.parse(''.join(open('./bashparse/test/features_test_code.txt').readlines()[3]))
		
		nodes = bashparse.parse('yep() { \n echo global vars: $i $j\n echo functional vars: $1\n }') \
				+ bashparse.parse('for i in 1 2; do \n for j in a b; do\n echo $i $j foo\n yep "$i .. $j"\n done\n done')
		
		#bashparse.parse(''.join(open('./bashparse/test/features_test_code.txt').readlines()[1:3]))
		for i, node in enumerate(nodes): nodes[i] = NodeVisitor(node).justify()
		function_dict = {}
		var_list = {}
		# function_dict = bashparse.build_function_dictionary(nodes, function_dict)
		unrolled_nodes = bashparse.build_and_resolve_fns(nodes, function_dict)
		#print()
		#for node in unrolled_nodes:
		#	print(node.dump())
		#print('\n\n\n')
		actual_results = []
		#print('unrolled nodes: ')
		for node in unrolled_nodes:
			# print(node.dump())
			var_list = bpvar.update_variable_list_with_node(node, var_list)
			
			actual_results += bpvar.replace_variables(node, var_list)
		#print('end unrolled nodes')
		#print()
		#print('expected:\n'+ expected_results[1].dump())
		#print('results:\n'+ actual_results[1].dump())
		#print(expected_results[1] == actual_results[1])
		#print('\n\n')
		#print('expected len: ', len(expected_results))
		"""
		for i in range(0, len(expected_results)):
			#print(expected_results[i].dump())
			#print(actual_results[i].dump())
			print()
			print('expected: ', expected_results[i].dump())
			print('results: ', actual_results[i].dump())
			print(expected_results[i] == actual_results[i])
			print('\n\n')
		"""
		self.assertTrue(expected_results == actual_results)
