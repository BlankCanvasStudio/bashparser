""" This file holds the definition of the template object """
import bashparse, copy


class Template:

    def __init__(self, text = '', chunks = [None], ratio = -1, raw_count = 1):
        if type(chunks) is not list: chunks = [chunks]
        self.text = text
        self.chunks = chunks
        self.ratio = ratio
            # The length of the template relative to the file 
            # This can be used to control the granulatiry of the templating system
        self.raw_count = raw_count  # raw number of times template has appeared
        self.weighted_count = (self.raw_count * self.ratio)  
            # Number of times a template has appeared weighted by the length of the template
            # We can use this to favor longer templates unless is occurs ALL the time
    
    def inc_counts(self, inc_num = 1):
        self.raw_count += inc_num
        self.weighted_count += (inc_num * self.ratio)
    
    def __str__(self):
        return 'Template("' + self.text + '", ratio: ' + str(self.ratio) + ', raw count: ' + str(self.raw_count) + ', weighted count: ' + str(self.raw_count * self.ratio) + ')'
    
    def __repr__(self):
        return 'Template("' + self.text + '", ratio: ' + str(self.ratio) + ', raw count: ' + str(self.raw_count) + ', weighted count: ' + str(self.raw_count * self.ratio) + ')'

    def __eq__(self, obj):
        return self.text == obj.text
    
    



# generate the templaces from chunks

def run_generate_templates(chunks, nodes):
    # primative turn every chunk into a template
    templates = []
    for slce in chunks:
        text = ''
        for i in range(slce.start[0], slce.end[0] + 1):
            text += str(NodeVisitor(nodes[i])) + ' ; '
        text = text[:-1]
        new_template = Template(text = text, chunks = [ slce ], ratio = ( ( slce.end[0] - slce.start[0] + 1 ) / len(nodes) ), raw_count = 1)
        if new_template not in templates: templates += [ copy.deepcopy(new_template) ]
        else: templates[templates.index(new_template)].inc_counts()
    return templates




# find the usefule templates

def run_find_useful_templates(template_record):
    # basic filtering alg: don't
    templates = []
    for key in template_record.keys():
        templates += [ template_record[key] ]
    
    return templates
