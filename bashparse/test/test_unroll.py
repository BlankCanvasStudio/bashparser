from unittest import TestCase
import bashparse 

class TestUnroll(TestCase):
    def test_basic_cmd_stripping(self):
        orig_string = """
echo this; echo that;
cd there;
dir | grep this;
"""
        nodes = bashparse.parse(orig_string)
        commands_stripped = bashparse.unroll.strip_cmd(nodes)
        commands_stripped = [ bashparse.justify(x) for x in commands_stripped ]
        
        correct_results = bashparse.parse('echo this') \
                        + bashparse.parse('echo that') \
                        + bashparse.parse('cd there') \
                        + bashparse.parse('dir | grep this')

        self.assertTrue(correct_results == commands_stripped)
