import bashlex, re

def node_level_regex(node:bashlex.ast.node, regex:str):
    matched_regexes = []
    if hasattr(node, 'parts'):
        for part in node.parts:
            matched_regexes += node_level_regex(part, regex)
    if hasattr(node, 'list'):
        for part in node.list:
            matched_regexes += node_level_regex(part, regex)
    if hasattr(node, 'output'):
        matched_regexes += node_level_regex(node.output, regex)
    if hasattr(node, 'word'):
        regex_hits = re.findall(regex, node.word)
        for hit in regex_hits:
            if hit[0] not in matched_regexes:  # The use of indexes here has to do with how re returns hits
                matched_regexes += [hit[0]]
    return list(set(matched_regexes))  # easy uniqueness