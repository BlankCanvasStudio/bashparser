from unittest import TestCase
from bashparse.ast import *
import bashlex

class TestAst(TestCase):

	def test_shift_ast_pos(self):
		# Test shift_ast_pos with single node
		node_string = "cd here; cd there"
		nodes = bashlex.parse(node_string)
		new_tree = shift_ast_pos(nodes[0], 1)
		expected_result = "ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(1, 3) word='cd'), WordNode(parts=[] pos=(4, 8) word='here')] pos=(1, 8)), OperatorNode(op=';' pos=(8, 9)), CommandNode(parts=[WordNode(parts=[] pos=(10, 12) word='cd'), WordNode(parts=[] pos=(13, 18) word='there')] pos=(10, 18))] pos=(1, 18))"
		self.assertTrue(len(new_tree) == 1)
		self.assertTrue(str(new_tree[0]) == expected_result)
		# Test shift_ast_pos with an array
		node_string = "cd here; cd there"
		nodes = bashlex.parse(node_string)
		new_tree = shift_ast_pos(nodes, 1)
		expected_result = "ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(1, 3) word='cd'), WordNode(parts=[] pos=(4, 8) word='here')] pos=(1, 8)), OperatorNode(op=';' pos=(8, 9)), CommandNode(parts=[WordNode(parts=[] pos=(10, 12) word='cd'), WordNode(parts=[] pos=(13, 18) word='there')] pos=(10, 18))] pos=(1, 18))"
		self.assertTrue(len(new_tree) == 1)
		self.assertTrue(str(new_tree[0]) == expected_result)
	def test_shift_ast_pos_to_start(self):
		# Test shift_ast_pos_to_start with single node
		node_string = "cd here; cd there"
		nodes = bashlex.parse(node_string)
		new_tree = shift_ast_pos_to_start(nodes[0].parts[2])
		expected_result = "CommandNode(parts=[WordNode(parts=[] pos=(0, 2) word='cd'), WordNode(parts=[] pos=(3, 8) word='there')] pos=(0, 8))"
		self.assertTrue(len(new_tree) == 1)
		self.assertTrue(expected_result == str(new_tree[0]))
		# Test shift_ast_pos_to_start with array
		node_string = "cd here; cd there"
		nodes = bashlex.parse(node_string)
		new_tree = shift_ast_pos_to_start(nodes[0].parts)
		expected_results = [
			"CommandNode(parts=[WordNode(parts=[] pos=(0, 2) word='cd'), WordNode(parts=[] pos=(3, 7) word='here')] pos=(0, 7))",
			"OperatorNode(op=';' pos=(7, 8))",
			"CommandNode(parts=[WordNode(parts=[] pos=(9, 11) word='cd'), WordNode(parts=[] pos=(12, 17) word='there')] pos=(9, 17))"	
		]
		for i in range(0, len(expected_results)):
			self.assertTrue(str(new_tree[i]) == expected_results[i])
	
	def test_execute_return_paths_to_node_type(self):
		# Test execute_return_paths_to_node_type
		node_string = "for a in $n\n do\n  wget that;\n cd there;\n mv here;\na=b;\n done"
		nodes = bashlex.parse(node_string)
		paths = execute_return_paths_to_node_type(nodes[0], [], [], 'assignment')
		expected_results = ["path_var([0,5,6,0], AssignmentNode(parts=[] pos=(50, 53) word='a=b'))"]
		for i in range(0, len(paths)):
			self.assertTrue(str(paths[i]) == expected_results[i])
		
	def test_return_paths_to_node_type(self):
		# Test return_paths_to_node_type 
		node_string = "for a in $n\n do\n  wget that;\n cd there;\n mv here;\na=b;\n done"
		nodes = bashlex.parse(node_string)
		paths = return_paths_to_node_type(nodes[0], 'word')
		expected_results = [
			"path_var([0,1], WordNode(parts=[] pos=(4, 5) word='a'))",
			"path_var([0,3], WordNode(parts=[ParameterNode(pos=(9, 11) value='n')] pos=(9, 11) word='$n'))", 
			"path_var([0,5,0,0], WordNode(parts=[] pos=(18, 22) word='wget'))", 
			"path_var([0,5,0,1], WordNode(parts=[] pos=(23, 27) word='that'))",
			"path_var([0,5,2,0], WordNode(parts=[] pos=(30, 32) word='cd'))", 
			"path_var([0,5,2,1], WordNode(parts=[] pos=(33, 38) word='there'))", 
			"path_var([0,5,4,0], WordNode(parts=[] pos=(41, 43) word='mv'))",
			"path_var([0,5,4,1], WordNode(parts=[] pos=(44, 48) word='here'))", 
		]
		
		for i in range(0, len(paths)):
			self.assertTrue(str(paths[i]) == expected_results[i])
			
	def test_return_variable_paths(self):
		# Test return_variable_paths
		node_string = "for a in $n\n do\n  wget that;\n cd there;\n mv $else;\na=b;\n done" 
		nodes = bashlex.parse(node_string)
		paths = return_variable_paths(nodes[0])
		expected_results = [
			"path_var([0,3,0], ParameterNode(pos=(9, 11) value='n'))",
			"path_var([0,5,4,1,0], ParameterNode(pos=(44, 49) value='else'))" 
		]
		for i in range(0, len(paths)):
			self.assertTrue(str(paths[i]) == expected_results[i])
	
	def test_convert_tree_to_string(self):
		node_string = "for a in $n\n do\n  wget that;\n cd there;\n mv here;\na=b;\n done"
		nodes = bashlex.parse(node_string)
		rebuilt_commands = convert_tree_to_string(nodes[0])
		expected_result = "for a in $n do wget that ; cd there ; mv here ; a=b ; done"
		self.assertTrue(rebuilt_commands == expected_result)
		
