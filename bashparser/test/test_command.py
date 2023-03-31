from unittest import TestCase
from bashparser.commands import *
import bashlex, bashparser

class TestVariables(TestCase):

	def test_build_alias_table(self):
		# Test that the mv moves get stored
		mv_node = bashlex.parse('mv one two')[0]
		cmd_alias_list = build_alias_table(mv_node, {})
		self.assertTrue(cmd_alias_list == {'two':'one'})  # Note that it should add mv_list automatically
        # Test that flags get ignored in the mv case
		mv_node = bashlex.parse('mv -f -q one two')[0]
		cmd_alias_list = build_alias_table(mv_node, {})
		self.assertTrue(cmd_alias_list == {'two':'one'})  # Note that it should add mv_list automatically
		# Test that the cmd without the / get added to
		mv_node = bashlex.parse('mv -f -q /usr/bin/one /usr/bin/two')[0]
		cmd_alias_list = build_alias_table(mv_node, {})
		self.assertTrue(cmd_alias_list == {'/usr/bin/two': '/usr/bin/one', 'two': 'one'})  # Note that it should add mv_list automatically
		# Test that the replacement works as well with the / involved
		mv_node = bashlex.parse('/usr/bin/two arguments')[0]
		replaced_node = resolve_aliasing(mv_node, cmd_alias_list)
		# expected_result = "CommandNode(parts=[WordNode(parts=[] pos=(0, 12) word='/usr/bin/one'), WordNode(parts=[] pos=(13, 22) word='arguments')] pos=(0, 22))"
		expected_result = bashlex.parse("/usr/bin/one arguments")
		self.assertTrue(expected_result == replaced_node)
		# Test that it works with arrays
		mv_node1 = bashlex.parse('/usr/bin/two arguments')[0]
		mv_node2 = bashlex.parse('two arguments2')[0]
		replaced_node = resolve_aliasing(mv_node1, cmd_alias_list) + resolve_aliasing(mv_node2, cmd_alias_list)
		expected_result = bashlex.parse("/usr/bin/one arguments") + bashlex.parse("one arguments2")
		self.assertTrue(expected_result == replaced_node) 
		# Test resolve node using the stuff above
		expected_result = bashlex.parse("mv /usr/bin/one /usr/bin/two") + bashlex.parse("/usr/bin/one arguments") + bashlex.parse("one arguments2")
		mv_node = bashlex.parse('mv /usr/bin/one /usr/bin/two') + [ mv_node1, mv_node2 ] 
		replaced_node = build_and_resolve_aliasing(mv_node, {})
		self.assertTrue(expected_result == replaced_node)
		# Testing if nesting works
		mv_node = bashlex.parse('mv /usr/bin/one /usr/bin/two; /usr/bin/two arguments; two arguments2')[0]
		replaced_nodes = build_and_resolve_aliasing(mv_node)
		expected_results = bashlex.parse('mv /usr/bin/one /usr/bin/two; /usr/bin/one arguments; one arguments2')
		self.assertTrue(replaced_nodes == expected_results)
		# Testing if redirect node replacement works 
		mv_node = bashlex.parse('mv /usr/bin/echo /tmp/hello;> /tmp/hello this')[0]
		replaced_nodes = build_and_resolve_aliasing(mv_node)
		replaced_nodes = [str(x) for x in replaced_nodes]
		expected_results = ["ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(0, 2) word='mv'), WordNode(parts=[] pos=(3, 16) word='/usr/bin/echo'), WordNode(parts=[] pos=(17, 27) word='/tmp/hello')] pos=(0, 27)), OperatorNode(op=';' pos=(27, 28)), CommandNode(parts=[RedirectNode(heredoc=None input=None output=WordNode(parts=[] pos=(30, 40) word='/usr/bin/echo') pos=(28, 40) type='>'), WordNode(parts=[] pos=(41, 45) word='this')] pos=(28, 45))] pos=(0, 45))"]
		self.assertTrue(replaced_nodes == expected_results)