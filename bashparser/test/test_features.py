""" This file is just going to test featuers that work in between files 
Basically just dedicated to edge cases that breaks the code. 
I need to make sure every new update keeps the important featuers"""

from unittest import TestCase
import bashparser
import bashparser.variables as bpvar
from bashparser import NodeVisitor
import os



class TestFeatures(TestCase):

	def test_scoping_unrolling_and_functions(self):
		expected_results = bashparser.parse('yep() { \n echo global vars: $i $j\n echo functional vars: $1\n }') \
							+ bashparser.parse('for i in 1 2; do \n for j in a b; do\n echo 1 a foo\n echo global vars: 1 a\n echo functional vars: "1 .. a" \n done\n done ') \
							+ bashparser.parse('for i in 1 2; do \n for j in a b; do\n echo 1 b foo\n echo global vars: 1 b\n echo functional vars: "1 .. b" \n done\n done ') \
							+ bashparser.parse('for i in 1 2; do \n for j in a b; do\n echo 2 a foo\n echo global vars: 2 a\n echo functional vars: "2 .. a" \n done\n done ') \
							+ bashparser.parse('for i in 1 2; do \n for j in a b; do\n echo 2 b foo\n echo global vars: 2 b\n echo functional vars: "2 .. b" \n done\n done ')

		for i, result in enumerate(expected_results):
			expected_results[i] = NodeVisitor(expected_results[i]).justify()
		
		nodes = bashparser.parse('yep() { \n echo global vars: $i $j\n echo functional vars: $1\n }') \
				+ bashparser.parse('for i in 1 2; do \n for j in a b; do\n echo $i $j foo\n yep "$i .. $j"\n done\n done')

		for i, node in enumerate(nodes): nodes[i] = NodeVisitor(node).justify()
		function_dict = {}
		var_list = {}
		unrolled_nodes = bashparser.build_and_resolve_fns(nodes, function_dict)

		actual_results = []
		for node in unrolled_nodes:
			var_list = bpvar.update_variable_list(node, var_list)
			actual_results += bpvar.replace_variables(node, var_list)

		self.assertTrue(expected_results == actual_results)
