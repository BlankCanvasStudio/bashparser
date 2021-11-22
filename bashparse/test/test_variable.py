from unittest import TestCase
from bashparse.variables import *
import bashlex

class TestVariables(TestCase):

    def test_update_trees_pos(self):
        self.assertRaises(ValueError, update_trees_pos, 'something', [], 0)
        self.assertRaises(ValueError, update_trees_pos, bashlex.parse('cd here')[0], 'something', 0)
        self.assertRaises(ValueError, update_trees_pos, bashlex.parse('cd here')[0], [], 'something')


    def test_update_command_substitution(self):
        self.assertRaises(ValueError, update_command_substitution, 'something')
    

    def test_replace_variables_using_paths(self):
        self.assertRaises(ValueError, replace_variables_using_paths, 'something', [], {})
        self.assertRaises(ValueError, replace_variables_using_paths, bashlex.parse('cd here')[0], 'something', {})
        self.assertRaises(ValueError, replace_variables_using_paths, bashlex.parse('cd here')[0], [], [])
    

    def test_substitute_variables(self):
        self.assertRaises(ValueError, substitute_variables, 'something', {})
        self.assertRaises(ValueError, substitute_variables, bashlex.parse('cd here')[0], [])
        # Testing for loops iterating over string, not variable
        test_str = 'for a in "one two three"\n do\n localgo\n cd $a\n done'
        for_node = bashlex.parse(test_str)[0]
        expected_results = [
            "CompoundNode(list=[ForNode(parts=[ReservedwordNode(pos=(0, 3) word='for'), WordNode(parts=[] pos=(4, 5) word='a'), ReservedwordNode(pos=(6, 8) word='in'), WordNode(parts=[] pos=(9, 22) word='one two three'), ReservedwordNode(pos=(26, 28) word='do'), ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(30, 37) word='localgo')] pos=(30, 37)), OperatorNode(op='\\n' pos=(37, 38)), CommandNode(parts=[WordNode(parts=[] pos=(39, 41) word='cd'), WordNode(parts=[] pos=(42, 45) word='one')] pos=(39, 45)), OperatorNode(op='\\n' pos=(44, 45))] pos=(30, 45)), ReservedwordNode(pos=(46, 50) word='done')] pos=(0, 50))] pos=(3, 50) redirects=[])",
            "CompoundNode(list=[ForNode(parts=[ReservedwordNode(pos=(0, 3) word='for'), WordNode(parts=[] pos=(4, 5) word='a'), ReservedwordNode(pos=(6, 8) word='in'), WordNode(parts=[] pos=(9, 22) word='one two three'), ReservedwordNode(pos=(26, 28) word='do'), ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(30, 37) word='localgo')] pos=(30, 37)), OperatorNode(op='\\n' pos=(37, 38)), CommandNode(parts=[WordNode(parts=[] pos=(39, 41) word='cd'), WordNode(parts=[] pos=(42, 45) word='two')] pos=(39, 45)), OperatorNode(op='\\n' pos=(44, 45))] pos=(30, 45)), ReservedwordNode(pos=(46, 50) word='done')] pos=(0, 50))] pos=(3, 50) redirects=[])",
            "CompoundNode(list=[ForNode(parts=[ReservedwordNode(pos=(0, 3) word='for'), WordNode(parts=[] pos=(4, 5) word='a'), ReservedwordNode(pos=(6, 8) word='in'), WordNode(parts=[] pos=(9, 22) word='one two three'), ReservedwordNode(pos=(26, 28) word='do'), ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(30, 37) word='localgo')] pos=(30, 37)), OperatorNode(op='\\n' pos=(37, 38)), CommandNode(parts=[WordNode(parts=[] pos=(39, 41) word='cd'), WordNode(parts=[] pos=(42, 47) word='three')] pos=(39, 47)), OperatorNode(op='\\n' pos=(44, 45))] pos=(30, 45)), ReservedwordNode(pos=(46, 50) word='done')] pos=(0, 50))] pos=(3, 50) redirects=[])"
        ]
        replaced_nodes = substitute_variables(for_node, {})

        replaced_nodes = [str(x) for x in replaced_nodes]
        self.assertTrue(expected_results == replaced_nodes)

    def test_variable_replacement_functions(self):
        # This code actually tests substitute_variables, update_trees_pos, update_command_substitution, and replace variables
        # It does this using well formatted inputs. Makes my life a lot easier
        
        # Verify that simple replacement of variables works
        var_list = {'var': ['one', 'two']}
        nodes = bashlex.parse('testing=$var')
        replaced_nodes = substitute_variables(nodes[0], var_list)
        replaced_nodes = [str(x) for x in replaced_nodes]
        result_string = [
            "CommandNode(parts=[AssignmentNode(parts=[] pos=(0, 11) word='testing=one')] pos=(0, 11))",
            "CommandNode(parts=[AssignmentNode(parts=[] pos=(0, 11) word='testing=two')] pos=(0, 11))"
        ]
        self.assertTrue(result_string == replaced_nodes)
        # Verify that command substitutions and variable replacements in that command substitution work
        var_list = {'http_server':['dns.cyberium.cc']}
        for_node_command_substitution_str = \
            "for a in $(cd $http_server)\n do\n rm -rf this\n done"
        for_node_command_substitution_parsed = \
            "CompoundNode(list=[ForNode(parts=[ReservedwordNode(pos=(0, 3) word='for'), WordNode(parts=[] pos=(4, 5) word='a'), ReservedwordNode(pos=(6, 8) word='in'), WordNode(parts=[CommandsubstitutionNode(command=CommandNode(parts=[WordNode(parts=[] pos=(11, 13) word='cd'), WordNode(parts=[] pos=(14, 29) word='dns.cyberium.cc')] pos=(11, 29)) pos=(11, 29))] pos=(11, 29) word='$(cd $http_server)'), ReservedwordNode(pos=(29, 31) word='do'), CommandNode(parts=[WordNode(parts=[] pos=(33, 35) word='rm'), WordNode(parts=[] pos=(36, 39) word='-rf'), WordNode(parts=[] pos=(40, 44) word='this')] pos=(33, 44)), ReservedwordNode(pos=(46, 50) word='done')] pos=(0, 50))] pos=(3, 50) redirects=[])"    
        nodes = bashlex.parse(for_node_command_substitution_str)
        results = substitute_variables(nodes[0], var_list)
        self.assertTrue(str(results[0]) == for_node_command_substitution_parsed)
        # Verify that a variable substitution will replace well and it will split into an array when necessary. Also lots of line breaks to make sure we can parse that
        for_loop_string_split = "for a in $n\n do\n\n rm -rf $a\n\n wget http://127.0.0.1/words/$a -O \n\n  chmod 777 $a\n ./$a ssh\n done"
        var_list = {'n':['arm arm5 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa']}
        for_node = bashlex.parse(for_loop_string_split)[0].list[0]  # To actually strip out just the for loop part
        result_strings = [
            "ForNode(parts=[ReservedwordNode(pos=(0, 3) word='for'), WordNode(parts=[] pos=(4, 5) word='a'), ReservedwordNode(pos=(6, 8) word='in'), WordNode(parts=[] pos=(9, 54) word='arm arm5 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'), ReservedwordNode(pos=(13, 15) word='do'), ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(18, 20) word='rm'), WordNode(parts=[] pos=(21, 24) word='-rf'), WordNode(parts=[] pos=(25, 28) word='arm')] pos=(18, 28)), OperatorNode(op='\\n' pos=(27, 28)), CommandNode(parts=[WordNode(parts=[] pos=(30, 34) word='wget'), WordNode(parts=[] pos=(35, 61) word='http://127.0.0.1/words/arm'), WordNode(parts=[] pos=(61, 63) word='-O')] pos=(30, 63)), OperatorNode(op='\\n' pos=(64, 65)), CommandNode(parts=[WordNode(parts=[] pos=(68, 73) word='chmod'), WordNode(parts=[] pos=(74, 77) word='777'), WordNode(parts=[] pos=(78, 81) word='arm')] pos=(68, 81)), OperatorNode(op='\\n' pos=(80, 81)), CommandNode(parts=[WordNode(parts=[] pos=(82, 87) word='./arm'), WordNode(parts=[] pos=(87, 90) word='ssh')] pos=(82, 90)), OperatorNode(op='\\n' pos=(90, 91))] pos=(18, 91)), ReservedwordNode(pos=(92, 96) word='done')] pos=(0, 96))",
            "ForNode(parts=[ReservedwordNode(pos=(0, 3) word='for'), WordNode(parts=[] pos=(4, 5) word='a'), ReservedwordNode(pos=(6, 8) word='in'), WordNode(parts=[] pos=(9, 54) word='arm arm5 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'), ReservedwordNode(pos=(13, 15) word='do'), ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(18, 20) word='rm'), WordNode(parts=[] pos=(21, 24) word='-rf'), WordNode(parts=[] pos=(25, 29) word='arm5')] pos=(18, 29)), OperatorNode(op='\\n' pos=(27, 28)), CommandNode(parts=[WordNode(parts=[] pos=(30, 34) word='wget'), WordNode(parts=[] pos=(35, 62) word='http://127.0.0.1/words/arm5'), WordNode(parts=[] pos=(61, 63) word='-O')] pos=(30, 63)), OperatorNode(op='\\n' pos=(64, 65)), CommandNode(parts=[WordNode(parts=[] pos=(68, 73) word='chmod'), WordNode(parts=[] pos=(74, 77) word='777'), WordNode(parts=[] pos=(78, 82) word='arm5')] pos=(68, 82)), OperatorNode(op='\\n' pos=(80, 81)), CommandNode(parts=[WordNode(parts=[] pos=(82, 88) word='./arm5'), WordNode(parts=[] pos=(87, 90) word='ssh')] pos=(82, 90)), OperatorNode(op='\\n' pos=(90, 91))] pos=(18, 91)), ReservedwordNode(pos=(92, 96) word='done')] pos=(0, 96))",
            "ForNode(parts=[ReservedwordNode(pos=(0, 3) word='for'), WordNode(parts=[] pos=(4, 5) word='a'), ReservedwordNode(pos=(6, 8) word='in'), WordNode(parts=[] pos=(9, 54) word='arm arm5 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'), ReservedwordNode(pos=(13, 15) word='do'), ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(18, 20) word='rm'), WordNode(parts=[] pos=(21, 24) word='-rf'), WordNode(parts=[] pos=(25, 61) word='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')] pos=(18, 61)), OperatorNode(op='\\n' pos=(27, 28)), CommandNode(parts=[WordNode(parts=[] pos=(30, 34) word='wget'), WordNode(parts=[] pos=(35, 94) word='http://127.0.0.1/words/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'), WordNode(parts=[] pos=(61, 63) word='-O')] pos=(30, 63)), OperatorNode(op='\\n' pos=(64, 65)), CommandNode(parts=[WordNode(parts=[] pos=(68, 73) word='chmod'), WordNode(parts=[] pos=(74, 77) word='777'), WordNode(parts=[] pos=(78, 114) word='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')] pos=(68, 114)), OperatorNode(op='\\n' pos=(80, 81)), CommandNode(parts=[WordNode(parts=[] pos=(82, 120) word='./aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'), WordNode(parts=[] pos=(87, 90) word='ssh')] pos=(82, 90)), OperatorNode(op='\\n' pos=(90, 91))] pos=(18, 91)), ReservedwordNode(pos=(92, 96) word='done')] pos=(0, 96))"
        ]
        replaced_nodes = substitute_variables(for_node, var_list)
        replaced_nodes = [str(x) for x in replaced_nodes]
        self.assertTrue(replaced_nodes == result_strings)
        # Test that list nodes replaced and returned properly 
        nodes = bashlex.parse('n=1;a=2$n')
        result_strings = ["ListNode(parts=[CommandNode(parts=[AssignmentNode(parts=[] pos=(0, 3) word='n=1')] pos=(0, 3)), OperatorNode(op=';' pos=(3, 4)), CommandNode(parts=[AssignmentNode(parts=[ParameterNode(pos=(7, 8) value='n')] pos=(7, 8) word='a=2$n')] pos=(7, 8))] pos=(0, 8))"]
        replaced_nodes = substitute_variables(nodes[0], {})
        replaced_nodes = [str(x) for x in replaced_nodes]
        self.assertTrue(replaced_nodes == result_strings)

    def test_add_variable_to_list(self):
        # Enforce that var_list is a dict
        self.assertRaises(ValueError, add_variable_to_list, [], 'something', [1, 2, 3])
        # Make sure that adding entries works if value is not not a string
        new_var_list = {}
        new_var_list = add_variable_to_list(new_var_list, 'name1', 1)
        self.assertTrue(new_var_list == {'name1':['1']})
        # Make sure that adding entries works if value is an array of not string, 
        new_var_list = {}
        new_var_list = add_variable_to_list(new_var_list, 'name1', [1, 2])
        self.assertTrue(new_var_list == {'name1':['1', '2']})
        # Make sure that adding entries works if value is str but not list
        new_var_list = {}
        new_var_list = add_variable_to_list(new_var_list, 'name1', 'value1')
        self.assertTrue(new_var_list == {'name1':['value1']})
        # Make sure adding non-list values works
        new_var_list = add_variable_to_list(new_var_list, 'name1', 'value2')
        self.assertTrue(new_var_list == {'name1':['value1', 'value2']})
        # Make sure that adding list values works
        new_var_list = add_variable_to_list(new_var_list, 'name1', ['value3', 'value4', 'value5'])
        self.assertTrue(new_var_list == {'name1':['value1', 'value2', 'value3', 'value4', 'value5']})
    

    def test_update_variable_list_with_node(self):
        node = bashlex.parse('a=b')[0]
        self.assertRaises(ValueError, update_variable_list_with_node, 'anything', {})
        self.assertRaises(ValueError, update_variable_list_with_node, node, [])
        # Test basic assignment gets saved
        mv_node = bashlex.parse('a=b')[0]
        new_var_list = update_variable_list_with_node(mv_node, {})
        self.assertTrue(new_var_list == {'a':['b']})  # Note that it should add mv_list automatically
        # Test command substitution assignment works fine
        mv_node = bashlex.parse('a=$(echo this)')[0]
        new_var_list = update_variable_list_with_node(mv_node, {})
        self.assertTrue(new_var_list == {'a':['$(echo this)']})  # Note that it should add mv_list automatically
        # Test that for loops work
        for_node = bashlex.parse('for a in "one two three"\n do\n echo something\n done')[0].list[0]
        new_var_list = update_variable_list_with_node(for_node, {})
        self.assertTrue(new_var_list == {'a':['one', 'two', 'three']})
        # Test for loops work with variable replacement
        for_node = bashlex.parse('for a in "$n"\n do\n echo something\n done')[0].list[0]
        new_var_list = update_var_list_with_for_loop(for_node, {'n':['one two three']})
        self.assertTrue(new_var_list == {'n':['one two three'], 'a':['one', 'two', 'three']})
        # Test for loops work with command substitution
        for_node = bashlex.parse('for a in "$(echo this)"\n do\n echo something\n done')[0].list[0]
        new_var_list = update_var_list_with_for_loop(for_node, {})
        self.assertTrue(new_var_list == {'a':['$(echo this)']})
    

    def test_update_var_list_with_for_loop(self):
        # Test that for loops work
        for_node = bashlex.parse('for a in "one two three"\n do\n echo something\n done')[0].list[0]
        new_var_list = update_variable_list_with_node(for_node, {})
        self.assertTrue(new_var_list == {'a':['one', 'two', 'three']})
        # Test for loops work with variable replacement
        for_node = bashlex.parse('for a in "$n"\n do\n echo something\n done')[0].list[0]
        new_var_list = update_var_list_with_for_loop(for_node, {'n':['one two three']})
        self.assertTrue(new_var_list == {'n':['one two three'], 'a':['one', 'two', 'three']})
        # Test for loops work with command substitution
        for_node = bashlex.parse('for a in "$(echo this)"\n do\n echo something\n done')[0].list[0]
        new_var_list = update_var_list_with_for_loop(for_node, {})
        self.assertTrue(new_var_list == {'a':['$(echo this)']})
        # Testing iterating over str, not variable

    
    def test_find_and_replace_variables(self):
        
        test_node = "n='one two three';\n for a in $n\n do\n cd $a; done"
        nodes = bashlex.parse(test_node)
        expected_results = [
            "ListNode(parts=[CommandNode(parts=[AssignmentNode(parts=[] pos=(0, 15) word='n=one two three')] pos=(0, 15)), OperatorNode(op=';' pos=(17, 18))] pos=(0, 18))",
            "CompoundNode(list=[ForNode(parts=[ReservedwordNode(pos=(20, 23) word='for'), WordNode(parts=[] pos=(24, 25) word='a'), ReservedwordNode(pos=(26, 28) word='in'), WordNode(parts=[] pos=(29, 42) word='one two three'), ReservedwordNode(pos=(33, 35) word='do'), ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(37, 39) word='cd'), WordNode(parts=[] pos=(40, 43) word='one')] pos=(37, 43)), OperatorNode(op=';' pos=(42, 43))] pos=(37, 43)), ReservedwordNode(pos=(44, 48) word='done')] pos=(20, 48))] pos=(23, 48) redirects=[])",
            "CompoundNode(list=[ForNode(parts=[ReservedwordNode(pos=(20, 23) word='for'), WordNode(parts=[] pos=(24, 25) word='a'), ReservedwordNode(pos=(26, 28) word='in'), WordNode(parts=[] pos=(29, 42) word='one two three'), ReservedwordNode(pos=(33, 35) word='do'), ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(37, 39) word='cd'), WordNode(parts=[] pos=(40, 43) word='one')] pos=(37, 43)), OperatorNode(op=';' pos=(42, 43))] pos=(37, 43)), ReservedwordNode(pos=(44, 48) word='done')] pos=(20, 48))] pos=(23, 48) redirects=[])"
            "CompoundNode(list=[ForNode(parts=[ReservedwordNode(pos=(20, 23) word='for'), WordNode(parts=[] pos=(24, 25) word='a'), ReservedwordNode(pos=(26, 28) word='in'), WordNode(parts=[] pos=(29, 42) word='one two three'), ReservedwordNode(pos=(44, 46) word='do'), ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(48, 50) word='cd'), WordNode(parts=[] pos=(51, 54) word='two')] pos=(48, 54)), OperatorNode(op=';' pos=(54, 55))] pos=(48, 55)), ReservedwordNode(pos=(56, 60) word='done')] pos=(20, 60))] pos=(20, 60) redirects=[])",
            "CompoundNode(list=[ForNode(parts=[ReservedwordNode(pos=(20, 23) word='for'), WordNode(parts=[] pos=(24, 25) word='a'), ReservedwordNode(pos=(26, 28) word='in'), WordNode(parts=[] pos=(29, 42) word='one two three'), ReservedwordNode(pos=(44, 46) word='do'), ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(48, 50) word='cd'), WordNode(parts=[] pos=(51, 56) word='three')] pos=(48, 56)), OperatorNode(op=';' pos=(56, 57))] pos=(48, 57)), ReservedwordNode(pos=(58, 62) word='done')] pos=(20, 62))] pos=(20, 62) redirects=[])"
        ]
        replaced_nodes = find_and_replace_variables(nodes)
        self.assertTrue(str(replaced_nodes[0]) == expected_results[0])
    
    def test_nested_for_loops(self):
        test_node = 'for i in 1 2 3\n do\n for j in 4 5\n do\n echo $i$j\n done\n done'
        nodes = bashlex.parse(test_node)
        expected_results  = ["CompoundNode(list=[ForNode(parts=[ReservedwordNode(pos=(0, 3) word='for'), WordNode(parts=[] pos=(4, 5) word='i'), ReservedwordNode(pos=(6, 8) word='in'), WordNode(parts=[] pos=(9, 10) word='1'), WordNode(parts=[] pos=(11, 12) word='2'), WordNode(parts=[] pos=(13, 14) word='3'), ReservedwordNode(pos=(16, 18) word='do'), CompoundNode(list=[ForNode(parts=[ReservedwordNode(pos=(20, 23) word='for'), WordNode(parts=[] pos=(24, 25) word='j'), ReservedwordNode(pos=(26, 28) word='in'), WordNode(parts=[] pos=(29, 30) word='4'), WordNode(parts=[] pos=(31, 32) word='5'), ReservedwordNode(pos=(34, 36) word='do'), CommandNode(parts=[WordNode(parts=[] pos=(38, 42) word='echo'), WordNode(parts=[] pos=(43, 45) word='14')] pos=(38, 45)), ReservedwordNode(pos=(49, 53) word='done')] pos=(20, 53))] pos=(3, 53) redirects=[]), ReservedwordNode(pos=(55, 59) word='done')] pos=(0, 59))] pos=(3, 59) redirects=[])", "CompoundNode(list=[ForNode(parts=[ReservedwordNode(pos=(0, 3) word='for'), WordNode(parts=[] pos=(4, 5) word='i'), ReservedwordNode(pos=(6, 8) word='in'), WordNode(parts=[] pos=(9, 10) word='1'), WordNode(parts=[] pos=(11, 12) word='2'), WordNode(parts=[] pos=(13, 14) word='3'), ReservedwordNode(pos=(16, 18) word='do'), CompoundNode(list=[ForNode(parts=[ReservedwordNode(pos=(20, 23) word='for'), WordNode(parts=[] pos=(24, 25) word='j'), ReservedwordNode(pos=(26, 28) word='in'), WordNode(parts=[] pos=(29, 30) word='4'), WordNode(parts=[] pos=(31, 32) word='5'), ReservedwordNode(pos=(34, 36) word='do'), CommandNode(parts=[WordNode(parts=[] pos=(38, 42) word='echo'), WordNode(parts=[] pos=(43, 45) word='15')] pos=(38, 45)), ReservedwordNode(pos=(49, 53) word='done')] pos=(20, 53))] pos=(3, 53) redirects=[]), ReservedwordNode(pos=(55, 59) word='done')] pos=(0, 59))] pos=(3, 59) redirects=[])", "CompoundNode(list=[ForNode(parts=[ReservedwordNode(pos=(0, 3) word='for'), WordNode(parts=[] pos=(4, 5) word='i'), ReservedwordNode(pos=(6, 8) word='in'), WordNode(parts=[] pos=(9, 10) word='1'), WordNode(parts=[] pos=(11, 12) word='2'), WordNode(parts=[] pos=(13, 14) word='3'), ReservedwordNode(pos=(16, 18) word='do'), CompoundNode(list=[ForNode(parts=[ReservedwordNode(pos=(20, 23) word='for'), WordNode(parts=[] pos=(24, 25) word='j'), ReservedwordNode(pos=(26, 28) word='in'), WordNode(parts=[] pos=(29, 30) word='4'), WordNode(parts=[] pos=(31, 32) word='5'), ReservedwordNode(pos=(34, 36) word='do'), CommandNode(parts=[WordNode(parts=[] pos=(38, 42) word='echo'), WordNode(parts=[] pos=(43, 45) word='24')] pos=(38, 45)), ReservedwordNode(pos=(49, 53) word='done')] pos=(20, 53))] pos=(3, 53) redirects=[]), ReservedwordNode(pos=(55, 59) word='done')] pos=(0, 59))] pos=(3, 59) redirects=[])", "CompoundNode(list=[ForNode(parts=[ReservedwordNode(pos=(0, 3) word='for'), WordNode(parts=[] pos=(4, 5) word='i'), ReservedwordNode(pos=(6, 8) word='in'), WordNode(parts=[] pos=(9, 10) word='1'), WordNode(parts=[] pos=(11, 12) word='2'), WordNode(parts=[] pos=(13, 14) word='3'), ReservedwordNode(pos=(16, 18) word='do'), CompoundNode(list=[ForNode(parts=[ReservedwordNode(pos=(20, 23) word='for'), WordNode(parts=[] pos=(24, 25) word='j'), ReservedwordNode(pos=(26, 28) word='in'), WordNode(parts=[] pos=(29, 30) word='4'), WordNode(parts=[] pos=(31, 32) word='5'), ReservedwordNode(pos=(34, 36) word='do'), CommandNode(parts=[WordNode(parts=[] pos=(38, 42) word='echo'), WordNode(parts=[] pos=(43, 45) word='25')] pos=(38, 45)), ReservedwordNode(pos=(49, 53) word='done')] pos=(20, 53))] pos=(3, 53) redirects=[]), ReservedwordNode(pos=(55, 59) word='done')] pos=(0, 59))] pos=(3, 59) redirects=[])", "CompoundNode(list=[ForNode(parts=[ReservedwordNode(pos=(0, 3) word='for'), WordNode(parts=[] pos=(4, 5) word='i'), ReservedwordNode(pos=(6, 8) word='in'), WordNode(parts=[] pos=(9, 10) word='1'), WordNode(parts=[] pos=(11, 12) word='2'), WordNode(parts=[] pos=(13, 14) word='3'), ReservedwordNode(pos=(16, 18) word='do'), CompoundNode(list=[ForNode(parts=[ReservedwordNode(pos=(20, 23) word='for'), WordNode(parts=[] pos=(24, 25) word='j'), ReservedwordNode(pos=(26, 28) word='in'), WordNode(parts=[] pos=(29, 30) word='4'), WordNode(parts=[] pos=(31, 32) word='5'), ReservedwordNode(pos=(34, 36) word='do'), CommandNode(parts=[WordNode(parts=[] pos=(38, 42) word='echo'), WordNode(parts=[] pos=(43, 45) word='34')] pos=(38, 45)), ReservedwordNode(pos=(49, 53) word='done')] pos=(20, 53))] pos=(3, 53) redirects=[]), ReservedwordNode(pos=(55, 59) word='done')] pos=(0, 59))] pos=(3, 59) redirects=[])", "CompoundNode(list=[ForNode(parts=[ReservedwordNode(pos=(0, 3) word='for'), WordNode(parts=[] pos=(4, 5) word='i'), ReservedwordNode(pos=(6, 8) word='in'), WordNode(parts=[] pos=(9, 10) word='1'), WordNode(parts=[] pos=(11, 12) word='2'), WordNode(parts=[] pos=(13, 14) word='3'), ReservedwordNode(pos=(16, 18) word='do'), CompoundNode(list=[ForNode(parts=[ReservedwordNode(pos=(20, 23) word='for'), WordNode(parts=[] pos=(24, 25) word='j'), ReservedwordNode(pos=(26, 28) word='in'), WordNode(parts=[] pos=(29, 30) word='4'), WordNode(parts=[] pos=(31, 32) word='5'), ReservedwordNode(pos=(34, 36) word='do'), CommandNode(parts=[WordNode(parts=[] pos=(38, 42) word='echo'), WordNode(parts=[] pos=(43, 45) word='35')] pos=(38, 45)), ReservedwordNode(pos=(49, 53) word='done')] pos=(20, 53))] pos=(3, 53) redirects=[]), ReservedwordNode(pos=(55, 59) word='done')] pos=(0, 59))] pos=(3, 59) redirects=[])"]
        replaced_nodes = substitute_variables(nodes, {})
        replaced_nodes = [str(x) for x in replaced_nodes]
        self.assertTrue(replaced_nodes == expected_results)
















