from unittest import TestCase
import bashparse

class TestChunk(TestCase):
    def test_variable_chunking(self):
        string_to_chunk="""
tmp=one
echo here
echo $tmp
cd there;
"""
        nodes = bashparse.parse(string_to_chunk)
        chunk = bashparse.find_variable_chunks(nodes)[0]
        self.assertTrue(chunk.start == [0,0])
        self.assertTrue(chunk.end == [2,1])