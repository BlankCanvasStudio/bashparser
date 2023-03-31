from unittest import TestCase
import bashparser

class TestChunk(TestCase):
    def test_variable_chunking(self):
        string_to_chunk="""
tmp=one
echo here
echo $tmp
cd there;
"""
        nodes = bashparser.parse(string_to_chunk)
        chunk = bashparser.find_variable_chunks(nodes)[0]
        self.assertTrue(chunk.start == [0,0])
        self.assertTrue(chunk.end == [2,1])