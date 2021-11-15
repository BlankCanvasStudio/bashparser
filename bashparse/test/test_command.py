from unittest import TestCase
from bashparse.commands import *
import bashlex, bashparse

class TestVariables(TestCase):

	def test_find_specific_commands(self):
		self.assertRaises(ValueError, find_specific_commands, 'this', ['str'], {}, bool)
		self.assertRaises(ValueError, find_specific_commands, bashlex.parse('this'), [1], {}, bool)
		self.assertRaises(ValueError, find_specific_commands, bashlex.parse('this'), 'str', {}, bool)
		self.assertRaises(ValueError, find_specific_commands, bashlex.parse('this'), ['str'], [], bool)
		self.assertRaises(ValueError, find_specific_commands, bashlex.parse('this'), ['str'], {}, 'str')
		# Test returning as string works fine
		command_string = "wget website.com"
		nodes = bashlex.parse(command_string)
		commands_looking_for = ['wget']
		expected_results_dictionary = {"wget": ['wget website.com']}
		saved_command_dictionary = find_specific_commands(nodes[0], commands_looking_for, {}, True)
		self.assertTrue(expected_results_dictionary == saved_command_dictionary)
		# Test returning as node works fine
		command_string = "wget website.com"
		nodes = bashlex.parse(command_string)
		commands_looking_for = ['wget']
		expected_results_dictionary = {"wget": [nodes[0]]}
		saved_command_dictionary = find_specific_commands(nodes[0], commands_looking_for, {}, False)
		self.assertTrue(expected_results_dictionary == saved_command_dictionary)
		# Verify that command substitutions work correctly
		command_string = "$(wget website.com)"
		nodes = bashlex.parse(command_string)
		command_substitution = nodes[0].parts[0].parts[0]
		commands_looking_for = ['wget']
		expected_results_dictionary = {"wget": ['wget website.com']}
		saved_command_dictionary = find_specific_commands(command_substitution, commands_looking_for, {}, True)
		self.assertTrue(expected_results_dictionary == saved_command_dictionary)
		# Test that compound nodes are parsed well
		command_string = "for a in $n\n do\n wget website.com\n wget othercite.com\n done"
		nodes = bashlex.parse(command_string)
		commands_looking_for = ['wget']
		expected_results_dictionary = {"wget": ['wget website.com','wget othercite.com']}
		saved_command_dictionary = find_specific_commands(nodes[0], commands_looking_for, {}, True)
		self.assertTrue(expected_results_dictionary == saved_command_dictionary)
		# Piggy back off the old results to make sure pure for loops work as well
		commands_looking_for = ['wget']
		expected_results_dictionary = {"wget": ['wget website.com','wget othercite.com']}
		saved_command_dictionary = find_specific_commands(nodes[0].list[0], commands_looking_for, {}, True)
		self.assertTrue(expected_results_dictionary == saved_command_dictionary)
		# Veryify that list nodes are parsed correctly
		command_string = "wget website.com; cd here; wget othercite2.com"
		nodes = bashlex.parse(command_string)
		commands_looking_for = ['wget']
		expected_results_dictionary = {"wget": ['wget website.com','wget othercite2.com']}
		saved_command_dictionary = find_specific_commands(nodes[0], commands_looking_for, {}, True)
		self.assertTrue(expected_results_dictionary == saved_command_dictionary)
		
	def test_return_commands_from_variable_delcaraction(self):
		self.assertRaises(ValueError, return_commands_from_variable_delcaraction, 'this')
		# Verify that it works for a regular assignment node
		nodes = bashlex.parse('a=$(wget this)')
		assignment_node = nodes[0].parts[0]
		commands = return_commands_from_variable_delcaraction(assignment_node)
		expected_str = "CommandNode(parts=[WordNode(parts=[] pos=(4, 8) word='wget'), WordNode(parts=[] pos=(9, 13) word='this')] pos=(4, 13))"
		self.assertTrue(str(commands[0]) == expected_str)
		# Test that it works for a complexly nested node. (This depends on return_path_to_node_type so as long as that works, so will this)
		nodes = bashlex.parse('a=$(wget this2)')
		commands = return_commands_from_variable_delcaraction(nodes[0])
		expected_str = "CommandNode(parts=[WordNode(parts=[] pos=(4, 8) word='wget'), WordNode(parts=[] pos=(9, 14) word='this2')] pos=(4, 14))"
		self.assertTrue(str(commands[0]) == expected_str)
	
	def test_return_commands_from_command_substitutions(self):
		self.assertRaises(ValueError, return_commands_from_command_substitutions, 'this')
		# Test assignment case works
		substitution_string = "testing=$(cd here)"
		expected_results = ["CommandNode(parts=[WordNode(parts=[] pos=(10, 12) word='cd'), WordNode(parts=[] pos=(13, 17) word='here')] pos=(10, 17))"]
		nodes = bashlex.parse(substitution_string)
		results = return_commands_from_command_substitutions(nodes[0])
		for i in range(0, len(results)):
			self.assertTrue(expected_results[i] == str(results[i]))
		# Test nested case works
		substitution_string = "testing=$(cd $(cd there))"
		nodes = bashlex.parse(substitution_string)
		expected_results = [
			"CommandNode(parts=[WordNode(parts=[] pos=(10, 12) word='cd'), WordNode(parts=[CommandsubstitutionNode(command=CommandNode(parts=[WordNode(parts=[] pos=(15, 17) word='cd'), WordNode(parts=[] pos=(18, 23) word='there')] pos=(15, 23)) pos=(13, 24))] pos=(13, 24) word='$(cd there)')] pos=(10, 24))", 
			"CommandNode(parts=[WordNode(parts=[] pos=(15, 17) word='cd'), WordNode(parts=[] pos=(18, 23) word='there')] pos=(15, 23))"
		]
		results = return_commands_from_command_substitutions(nodes[0])
		for i in range(0, len(results)):
			self.assertTrue(expected_results[i] == str(results[i]))
		# Test for loops
		substitution_string = "for x in $(cd here)\n do\n wget there\n done"
		expected_results = ["CommandNode(parts=[WordNode(parts=[] pos=(11, 13) word='cd'), WordNode(parts=[] pos=(14, 18) word='here')] pos=(11, 18))"]
		nodes = bashlex.parse(substitution_string)
		results = return_commands_from_command_substitutions(nodes[0])
		for i in range(0, len(results)):
			self.assertTrue(expected_results[i] == str(results[i]))
	
	def test_return_commands_from_for_loops(self):
		test_string = "for a in $n\n do\n echo this; echo that\n done"
		node = bashlex.parse(test_string)[0]
		expected_results = [ 
			"CommandNode(parts=[WordNode(parts=[] pos=(17, 21) word='echo'), WordNode(parts=[] pos=(22, 26) word='this')] pos=(17, 26))",
			"CommandNode(parts=[WordNode(parts=[] pos=(28, 32) word='echo'), WordNode(parts=[] pos=(33, 37) word='that')] pos=(28, 37))"
		]
		results = return_commands_from_for_loops(node)
		for i in range(0, len(expected_results)):
			self.assertTrue(expected_results[i] == str(results[i]))

	def test_return_command_aliasing(self):
		# Test that the mv moves get stored
		mv_node = bashlex.parse('mv one two')[0]
		cmd_alias_list = return_command_aliasing(mv_node, {})
		self.assertTrue(cmd_alias_list == {'two':'one'})  # Note that it should add mv_list automatically
        # Test that flags get ignored in the mv case
		mv_node = bashlex.parse('mv -f -q one two')[0]
		cmd_alias_list = return_command_aliasing(mv_node, {})
		self.assertTrue(cmd_alias_list == {'two':'one'})  # Note that it should add mv_list automatically
		# Test that the cmd without the / get added to
		mv_node = bashlex.parse('mv -f -q /usr/bin/one /usr/bin/two')[0]
		cmd_alias_list = return_command_aliasing(mv_node, {})
		self.assertTrue(cmd_alias_list == {'/usr/bin/two': '/usr/bin/one', 'two': 'one'})  # Note that it should add mv_list automatically
		# Test that the replacement works as well with the / involved
		mv_node = bashlex.parse('/usr/bin/two arguments')[0]
		replaced_node = replace_command_aliasing(mv_node, cmd_alias_list)
		expected_result = "CommandNode(parts=[WordNode(parts=[] pos=(0, 12) word='/usr/bin/one'), WordNode(parts=[] pos=(13, 22) word='arguments')] pos=(0, 22))"
		self.assertTrue(expected_result == str(replaced_node[0]))
		# Test that it works with arrays
		mv_node = [ bashlex.parse('/usr/bin/two arguments')[0], bashlex.parse('two arguments2')[0] ]
		replaced_node = replace_command_aliasing(mv_node, cmd_alias_list)
		replaced_node = [str(x) for x in replaced_node]
		expected_result = [
			"CommandNode(parts=[WordNode(parts=[] pos=(0, 12) word='/usr/bin/one'), WordNode(parts=[] pos=(13, 22) word='arguments')] pos=(0, 22))", 
			"CommandNode(parts=[WordNode(parts=[] pos=(0, 3) word='one'), WordNode(parts=[] pos=(4, 14) word='arguments2')] pos=(0, 14))"
		]
		self.assertTrue(expected_result == replaced_node) 
		# Test resolve node using the stuff above
		expected_result = [
			"CommandNode(parts=[WordNode(parts=[] pos=(0, 2) word='mv'), WordNode(parts=[] pos=(3, 15) word='/usr/bin/one'), WordNode(parts=[] pos=(16, 28) word='/usr/bin/two')] pos=(0, 28))", 
			"CommandNode(parts=[WordNode(parts=[] pos=(0, 12) word='/usr/bin/one'), WordNode(parts=[] pos=(13, 22) word='arguments')] pos=(0, 22))", 
			"CommandNode(parts=[WordNode(parts=[] pos=(0, 3) word='one'), WordNode(parts=[] pos=(4, 14) word='arguments2')] pos=(0, 14))"
		]
		mv_node = bashlex.parse('mv /usr/bin/one /usr/bin/two') + mv_node
		replaced_node = resolve_command_aliasing(mv_node, {})
		replaced_node = [str(x) for x in replaced_node]
		self.assertTrue(expected_result == replaced_node)
		# Testing if nesting works
		mv_node = bashlex.parse('mv /usr/bin/one /usr/bin/two; /usr/bin/two arguments; two arguments2')[0]
		replaced_nodes = resolve_command_aliasing(mv_node)
		replaced_nodes = [str(x) for x in replaced_nodes]
		expected_results = ["ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(0, 2) word='mv'), WordNode(parts=[] pos=(3, 15) word='/usr/bin/one'), WordNode(parts=[] pos=(16, 28) word='/usr/bin/two')] pos=(0, 28)), OperatorNode(op=';' pos=(28, 29)), CommandNode(parts=[WordNode(parts=[] pos=(30, 42) word='/usr/bin/one'), WordNode(parts=[] pos=(43, 52) word='arguments')] pos=(30, 52)), OperatorNode(op=';' pos=(52, 53)), CommandNode(parts=[WordNode(parts=[] pos=(54, 57) word='one'), WordNode(parts=[] pos=(58, 68) word='arguments2')] pos=(54, 68))] pos=(0, 68))"]
		self.assertTrue(replaced_nodes == expected_results)
