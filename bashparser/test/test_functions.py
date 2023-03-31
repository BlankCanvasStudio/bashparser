from unittest import TestCase
import bashparser

class TestFunctions(TestCase):
    def test_build_fn_table(self):
        fn_node = bashparser.parse('somefn () { echo this; cd that; echo else; }')[0]
        fn_table = bashparser.build_fn_table(fn_node)
        self.assertTrue(bashparser.parse('echo this; cd that; echo else;')[0] == fn_table['somefn'])
    
    def test_resolve_functions(self):
        # This test actually covers both the replacement case AND the event where the top level node is the one to be replaced. very good
        fn_node = bashparser.parse('somefn () { echo $1; cd there; }')[0]
        fn_table = bashparser.build_fn_table(fn_node)
        calling_node = bashparser.parse('somefn an_argument')[0]
        resolved_node = bashparser.resolve_functions(calling_node, fn_table)[0]
        proper_resolution = bashparser.parse('echo an_argument; cd there;')[0]
        self.assertTrue(resolved_node == proper_resolution)
    
    def test_build_and_resolve_fn(self):
        # Tests nested replacement and build&resolve fn. 
        # Note the extra space at the end of the function replacement in correctly_resolved_node. Intentional cause keeping the spacing is way too hard for what its worth. Might need some consistency around it though
        fn_node = bashparser.parse('somefn () { echo $1; cd there; }')[0]
        calling_node = bashparser.parse('for a in $(dir); do somefn an_argument; done')[0]
        nodes = [ fn_node ] + [ calling_node ]
        resolved_nodes = bashparser.build_and_resolve_fns(nodes)
        correctly_resolved_node = bashparser.parse('for a in $(dir); do echo an_argument; cd there ; done')[0]
        self.assertTrue(resolved_nodes[1] == correctly_resolved_node)