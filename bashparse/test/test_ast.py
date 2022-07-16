from unittest import TestCase
from bashparse.ast import *
import bashlex

class TestAst(TestCase):

	def test_align(self):
		# Test align with single node
		node_string = "cd here; cd there"
		nodes = bashlex.parse(node_string)
		tmp = align(nodes[0], 1)
		expected_result = "ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(1, 3) word='cd'), WordNode(parts=[] pos=(4, 8) word='here')] pos=(1, 8)), OperatorNode(op=';' pos=(8, 9)), CommandNode(parts=[WordNode(parts=[] pos=(10, 12) word='cd'), WordNode(parts=[] pos=(13, 18) word='there')] pos=(10, 18))] pos=(1, 18))"
		self.assertTrue(str(tmp) == expected_result)
		# Test align with an array
		node_string = "cd here; cd there"
		nodes = bashlex.parse(node_string)
		new_tree = align(nodes[0], 1)
		expected_result = "ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(1, 3) word='cd'), WordNode(parts=[] pos=(4, 8) word='here')] pos=(1, 8)), OperatorNode(op=';' pos=(8, 9)), CommandNode(parts=[WordNode(parts=[] pos=(10, 12) word='cd'), WordNode(parts=[] pos=(13, 18) word='there')] pos=(10, 18))] pos=(1, 18))"
		self.assertTrue(str(new_tree) == expected_result)
	def test_justify(self):
		# Test justify with single node
		node_string = "cd here; cd there"
		nodes = bashlex.parse(node_string)
		new_tree = justify(nodes[0].parts[2])
		expected_result = "CommandNode(parts=[WordNode(parts=[] pos=(0, 2) word='cd'), WordNode(parts=[] pos=(3, 8) word='there')] pos=(0, 8))"
		self.assertTrue(expected_result == str(new_tree))
		# Test justify with array
		node_string = "cd here; cd there"
		nodes = bashlex.parse(node_string)
		new_tree = [] 
		for part in nodes[0].parts:
			new_tree += [ justify(part) ]
		expected_results = bashlex.parse("cd here") + ["OperatorNode(op=';' pos=(0, 1))"] + bashlex.parse("cd there")
		for i in range(0, len(expected_results)):
			self.assertTrue(str(new_tree[i]) == str(expected_results[i]))

	def test_convert_tree_to_string(self):
		node_string = "for a in $n\n do\n  wget that;\n cd there;\n mv here;\na=b;\n done"
		nodes = bashlex.parse(node_string)
		rebuilt_commands = str(NodeVisitor(nodes[0]))
		expected_result = "for a in $n do wget that ; cd there ; mv here ; a=b ; done"
		self.assertTrue(rebuilt_commands == expected_result)
		
