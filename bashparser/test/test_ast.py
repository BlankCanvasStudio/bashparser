from unittest import TestCase
from bashparser import NodeVisitor
import bashlex, bashparser.ast, copy

class TestAst(TestCase):


	def test_align(self):
		# Test align with single node
		node_string = "cd here; cd there"
		nodes = bashlex.parse(node_string)
		tmp = NodeVisitor(nodes[0]).align(delta=1)
		expected_result = "ListNode(parts=[CommandNode(parts=[WordNode(parts=[] pos=(1, 3) word='cd'), WordNode(parts=[] pos=(4, 8) word='here')] pos=(1, 8)), OperatorNode(op=';' pos=(8, 9)), CommandNode(parts=[WordNode(parts=[] pos=(10, 12) word='cd'), WordNode(parts=[] pos=(13, 18) word='there')] pos=(10, 18))] pos=(1, 18))"
		self.assertTrue(str(tmp) == expected_result)


	def test_justify(self):
		# Test justify with single node
		node_string = "cd here; cd there"
		nodes = bashlex.parse(node_string)
		new_tree = NodeVisitor(nodes[0].parts[2]).justify()
		expected_result = "CommandNode(parts=[WordNode(parts=[] pos=(0, 2) word='cd'), WordNode(parts=[] pos=(3, 8) word='there')] pos=(0, 8))"
		self.assertTrue(expected_result == str(new_tree))
		# Test justify with array
		node_string = "cd here; cd there"
		nodes = bashlex.parse(node_string)
		new_tree = [] 
		for part in nodes[0].parts:
			new_tree += [ NodeVisitor(part).justify() ]
		expected_results = bashlex.parse("cd here") + ["OperatorNode(op=';' pos=(0, 1))"] + bashlex.parse("cd there")
		for i in range(0, len(expected_results)):
			self.assertTrue(str(new_tree[i]) == str(expected_results[i]))


	def test_str(self):
		node_string = "for a in $n\n do\n  wget that;\n cd there;\n mv here;\na=b;\n done"
		nodes = bashlex.parse(node_string)
		rebuilt_commands = str(NodeVisitor(nodes[0]))
		expected_result = "for a in $n do wget that ; cd there ; mv here ; a=b ; done"
		self.assertTrue(rebuilt_commands == expected_result)
		self.assertTrue(str(NodeVisitor(None)) == '')
		"""
		node_string = 'history -n >/dev/null 2>&1'
		node = bashlex.parse(node_string)[0]
		rebuilt_command = str(NodeVisitor(node))
		expected_result = 'history -n >/dev/null 2>&1'
		self.assertTrue(rebuilt_command == expected_result)
		"""

	def test_apply(self):
		# Build ast to test apply on
		children = []
		root = bashlex.ast.node(kind='word', word = 'test', parts=[], pos=(0,4))
		for _ in range(0,3): children += [copy.deepcopy(root)]
		setattr(root, 'parts', copy.deepcopy(children))
		for i, child in enumerate(root.parts): setattr(child, 'parts', copy.deepcopy(children[:i]))
		vstr = NodeVisitor(root)

		# Change the values so that we can visually see how apply is working
		def apply_fn(node, vstr):
			if vstr.path == [1]: 
				node.word = 'DONT_DESCEND'
				return bashparser.ast.DONT_DESCEND
			elif vstr.path == [2,0]:
				node.word = 'HALT'
				return bashparser.ast.HALT
			else:
				node.word = 'TOUCHED'
				return bashparser.ast.CONT
		vstr.apply(apply_fn, vstr)

		# build correct solution by hand so bugs don't interfere with eachother
		expected_results = bashlex.ast.node(kind='word', word = 'TOUCHED', parts=[], pos=(0,4))
		
		dont_descend_node = bashlex.ast.node(kind='word', word='DONT_DESCEND', parts=[], pos=(0,4))
		dont_descend_node.parts += [ bashlex.ast.node(kind='word', word = 'test', parts=[], pos=(0,4))  ]
		
		halt_node = bashlex.ast.node(kind='word', word='TOUCHED', pos=(0,4), parts=[])
		halt_node.parts += [ bashlex.ast.node(kind='word', word='HALT', pos=(0,4), parts=[]) ]
		halt_node.parts += [ bashlex.ast.node(kind='word', word = 'test', parts=[], pos=(0,4)) ]

		expected_results.parts += [ copy.deepcopy(expected_results) ]
		expected_results.parts += [ dont_descend_node ]
		expected_results.parts += [ halt_node ]

		# Check to see if it worked
		self.assertTrue(vstr.root == expected_results)
		pass


	def test_expand_ast_along_path(self):
		# Generate nodes to expand
		children = []
		root = bashlex.ast.node(kind='word', word = 'test', parts=[], pos=(0,4))
		for _ in range(0,8): children += [copy.deepcopy(root)]
		setattr(root, 'parts', copy.deepcopy(children))
		for i, child in enumerate(root.parts): setattr(child, 'parts', copy.deepcopy(children[:i]))
		vstr = NodeVisitor(root)
		# Expand the ast
		bashparser.ast.expand_ast_along_path(root, [5,3], 2)
		# Verify the expansion
		def apply_fn(node, vstr):
			path_expanded_on = [5,3]
			length = len(vstr.path) if len(vstr.path) < 2 else 2
			if vstr.path[:length] == path_expanded_on[:length]:
				self.assertTrue(node.pos == (0,6))
			else:
				self.assertTrue(node.pos == (0,4))
		vstr.apply(apply_fn, vstr)


	def test_applys_on_path(self):
		# Build a basic ast
		root = bashlex.ast.node(kind='word', word='test', parts=[], pos=(0,4))
		children = []
		for _ in range(0,5): children += [ copy.deepcopy(root) ]
		vstr = NodeVisitor(root)
		vstr.set_children(children=copy.deepcopy(children))
		for child in vstr.children(): vstr.set_children(child, copy.deepcopy(children[:3]))

		# Apply the functions to the ast
		path = [4,1]
		def apply_fn_right(node): node.word = 'right'
		def apply_fn_path(node): node.word = 'path'
		def apply_fn_left(node): node.word = 'left'
		vstr.apply_along_path(apply_fn_path, path)
		vstr.apply_right_of_path(apply_fn_right, path)
		vstr.apply_left_of_path(apply_fn_left, path)
		
		# Build the expected nodes by hand so no bugs can interact (hopefully)
		expected_results = bashlex.ast.node(kind='word', word='path', pos=(0,4), parts=[])
		left_child = bashlex.ast.node(kind='word', word='left', pos=(0,4), parts=[])
		new_parts = []
		for i in range(0, 4): 
			new_child = copy.deepcopy(left_child)
			for j in range(0,3):
				new_child.parts += [copy.deepcopy(left_child)]
			new_parts += [ new_child ]
		final_node = bashlex.ast.node(kind='word', word='path', pos=(0,4), parts=[])
		final_node.parts += [ bashlex.ast.node(kind='word', word='left', pos=(0,4), parts=[]) ]
		final_node.parts += [ bashlex.ast.node(kind='word', word='path', pos=(0,4), parts=[]) ]
		final_node.parts += [ bashlex.ast.node(kind='word', word='right', pos=(0,4), parts=[]) ]
		new_parts += [ final_node ]		
		vstr.set_children(expected_results, new_parts)

		# Verify the two trees are equal
		self.assertTrue(vstr.root == expected_results)


	def test_at_path(self):
		children = []
		root = bashlex.ast.node(kind='word', word = 'test', parts=[], pos=(0,4))
		for _ in range(0,3): children += [copy.deepcopy(root)]
		children = children[:1] + [ bashlex.ast.node(kind='word', word='injected') ] + children[1:]
		setattr(root, 'parts', copy.deepcopy(children))		

		node_returned = NodeVisitor(root).at_path(path=[1])
		self.assertTrue(node_returned == bashlex.ast.node(kind='word', word='injected'))


	def test_children(self):
		children = []
		root = bashlex.ast.node(kind='word', word = 'test', parts=[], pos=(0,4))
		for _ in range(0,3): children += [copy.deepcopy(root)]
		setattr(root, 'parts', copy.deepcopy(children))
		
		# Verify NodeVisitor.children works
		children_returned = NodeVisitor(root).children()
		self.assertTrue(children_returned == children)

		# Verify NodeVisitor.set_children works
		children = children[:1] + [ bashlex.ast.node(kind='word', word='injected') ] + children[1:]
		NodeVisitor(root).set_children(children=copy.deepcopy(children))
		children_returned = NodeVisitor(root).children()
		self.assertTrue(children_returned == children)

		# Veryfiy that NodeVisitor.child works
		child_returned = NodeVisitor(root).child(num=1)
		self.assertTrue(child_returned == bashlex.ast.node(kind='word', word='injected') )


	def test_swap_node(self):
		children = []
		root = bashlex.ast.node(kind='word', word = 'test', parts=[], pos=(0,4))
		for _ in range(0,3): children += [copy.deepcopy(root)]
		# children = children[:1] + [ bashlex.ast.node(kind='word', word='injected') ] + children[1:]
		setattr(root, 'parts', copy.deepcopy(children))		

		NodeVisitor(root).swap_node(root=root, path=[1], child = bashlex.ast.node(kind='word', word='injected', pos=(3,12), parts=[]))
		node_returned = NodeVisitor(root).child(num=1)
		self.assertTrue(node_returned == bashlex.ast.node(kind='word', word='injected', pos=(0,9), parts=[]))		# Note the alignment of the pos attr


	def test_remove(self):
		children = []
		root = bashlex.ast.node(kind='word', word = 'test', parts=[], pos=(0,4))
		for _ in range(0,3): children += [copy.deepcopy(root)]
		injected_children = children[:1] + [ bashlex.ast.node(kind='word', word='injected') ] + children[1:]
		setattr(root, 'parts', copy.deepcopy(injected_children))
		NodeVisitor(root).remove(path=[1])
		self.assertTrue(NodeVisitor(root).children() == children)
		

	def test_replace(self):
		children = []
		root = bashlex.ast.node(kind='word', word = 'test', parts=[], pos=(0,4))
		for _ in range(0,3): children += [copy.deepcopy(root)]
		setattr(root, 'parts', copy.deepcopy(children))

		def qual_fn(node, vstr):
			if vstr.path == [2]: return True
			return False
		def gen_fn(node):
			new_nodes = []
			new_nodes += [ bashlex.ast.node(kind='assignment', word='0', pos=(0,4), parts=[]) ]
			new_nodes += [ bashlex.ast.node(kind='assignment', word='1', pos=(0,4), parts=[]) ]
			new_nodes += [ bashlex.ast.node(kind='assignment', word='2', pos=(0,4), parts=[]) ]
			return new_nodes

		vstr = NodeVisitor(root)
		new_nodes = vstr.replace(qual_fn, {'vstr':vstr}, gen_fn, {})
		for i, el in enumerate(new_nodes):
			self.assertTrue(el.parts == (children[:2] + [ bashlex.ast.node(kind='assignment', word=str(i), pos=(0,4), parts=[]) ] + children[3:] ))
















































