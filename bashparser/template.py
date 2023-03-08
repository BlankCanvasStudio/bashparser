#!/bin/python3
""" This file holds the definition of the template object """
import bashparser.unroll as unroll
import copy 
from bashparser.chunk import *
from bashparser.generalize import *


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
def generate_templates(nodes):
    """ This function takes an array of nodes and returns the templates generated """

    if type(nodes) is not list: nodes = [nodes]

    chunks = find_variable_chunks(nodes)
    chunks += find_cd_chunks(nodes)
    nodes = generalize_nodes(nodes) 
        # Make sure to generalize last. You'll make searching really buggy
    
    # Actually count all the templates
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


def add_templates(templates, template_record):
    """ This function takes in the templates & current template records and returns the updated 
    template_record object. It adds all templates to the template_record object. The record object 
    is going to be used to idetify any important templates / trends. """

    for template in templates:
        if template.text in template_record: template_record[template.text].inc_counts(inc_num = template.raw_count) 
        else: template_record[template.text] = template

    return template_record


def templatize(nodes, template_record = {}):
    """updates the template_record
    object with all of the templates found in the files. Returns the template_record object (dict) """

    # We generate 3 kinds of nodes to draw templates from: 
        # originally parsed nodes, variables replaced nodes, and the unrolled nodes 
    var_list = bashparser.update_variable_list_with_node(nodes)
    replaced_nodes = bashparser.substitute_variables(nodes, var_list)
    unrolled_nodes = unroll.replacement_unroll(nodes, var_list = {})

    # Generate the templates from each sequence of nodes
    templates = generate_templates(nodes)
    templates += generate_templates(replaced_nodes)
    templates += generate_templates(unrolled_nodes)

    # Add the new templates to the records
    template_record = add_templates(templates, template_record)

    return template_record