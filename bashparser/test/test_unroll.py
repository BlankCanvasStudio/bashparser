from unittest import TestCase
import bashparser 

class TestUnroll(TestCase):
    def test_basic_cmd_stripping(self):
        orig_string = """
echo this; echo that;
cd there;
dir | grep this;
"""
        nodes = bashparser.parse(orig_string)
        commands_stripped = bashparser.unroll.strip_cmd(nodes)
        commands_stripped = [ bashparser.justify(x) for x in commands_stripped ]
        
        correct_results = bashparser.parse('echo this') \
                        + bashparser.parse('echo that') \
                        + bashparser.parse('cd there') \
                        + bashparser.parse('dir | grep this')

        self.assertTrue(correct_results == commands_stripped)
