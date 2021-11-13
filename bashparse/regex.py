import bashlex, re

def node_level_regex(nodes, regex):
    """(nodes, regex string). This will find all occurances of a regex in a given nodes of the ast
	Could expand this to regex multiple nodess of ast but that's not really useful as of now and ast intepretation
	would achieve the same, if not a better result"""
    if type(nodes) is not list: nodes = [nodes]
    for el in nodes: 
        if type(el) is not bashlex.ast.node: raise ValueError('nodes must be made up of bashlex.ast.node objects')
    matched_regexes = []
    for node in nodes:
        if hasattr(node, 'parts'):
            for part in node.parts:
                new_regexes = node_level_regex(part, regex)
                for reg in new_regexes:
                    if reg not in matched_regexes: matched_regexes += [reg]
        if hasattr(node, 'list'):
            for part in node.list:
                new_regexes = node_level_regex(part, regex)
                for reg in new_regexes:
                    if reg not in matched_regexes: matched_regexes += [reg]
        if hasattr(node, 'output'):
            new_regexes = node_level_regex(node.output, regex)
            for reg in new_regexes:
                if reg not in matched_regexes: matched_regexes += [reg]
        if hasattr(node, 'word'):
            regex_hits = re.findall(regex, node.word)
            for hit in regex_hits:  # This is questionable but I'll leave it
                if hit not in matched_regexes and hit:  # The use of indexes here has to do with how re returns hits
                    matched_regexes += [hit]
    return matched_regexes #list(set(matched_regexes))  # easy uniqueness