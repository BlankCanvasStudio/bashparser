import bashparse.unroll as unroll
import copy 
from bashparse.chunk import *
from bashparse.generalize import *
from bashparse.template import *

"""
    Logical structure:  ( loop until done ){ generate_templates -> filter_templates -> add_templates } -> find_useful_templates -> QED
"""


def generalize_nodes(nodes):
    """ This function takes nodes and returns their most general form 
    (ie without using specific parameters). This will return a list of nodes """
    
    if type(nodes) is not list: nodes = [nodes]
    
    generalized_nodes = copy.deepcopy(nodes)
    generalized_nodes = run_generalize_nodes(generalized_nodes)

    return generalized_nodes


def generate_template_chunks(nodes):
    """ This is going to take an array of nodes and identify and group all the chunks in 
    node list, returning the chunks it deems valuable. This does not necessariuly return ALL 
    the possible chunks, only the chunks it cares about """
    
    if type(nodes) is not list: nodes = [nodes]
    
    template_chunks = run_identify_chunks(nodes)

    return template_chunks


def generate_templates(nodes):
    """ This function takes an array of nodes and returns the templates generated """
    
    if type(nodes) is not list: nodes = [nodes]
    
    chunks = generate_template_chunks(nodes)
    nodes = generalize_nodes(nodes) 
        # Make sure to generalize last. You'll make searching really buggy
    templates = run_generate_templates(chunks, nodes)

    return templates


def filter_templates(templates):
    """ This takes an array of templates and returns on the necessary templates from 
    the complete list of templates generated. This is separated from generate_templates 
    for modularity and to allow filtering to be a different concept from the generation """

    filtered_templates = copy.deepcopy(templates)

    return filtered_templates


def add_templates(templates, template_record):
    """ This function takes in the templates & current template records and returns the updated 
    template_record object. It adds all templates to the template_record object. The record object 
    is going to be used to idetify any important templates / trends. """
    
    for template in templates:
        if template.text in template_record: template_record[template.text].inc_counts(inc_num = template.raw_count) 
        else: template_record[template.text] = template

    return template_record


def find_useful_templates(template_record):
    """ This function takes the template_record and returns an array of any templates deemed to be useful """
    
    useful_templates = run_find_useful_templates(template_record)
    
    return useful_templates


def templatize(nodes, template_record = {}):
    """updates the template_record
    object with all of the templates found in the files. Returns the template_record object (dict) """
    
    # We generate 3 kinds of nodes to draw templates from: 
        # originally parsed nodes, variables replaced nodes, and the unrolled nodes 
    var_list = bashparse.update_variable_list_with_node(nodes)
    replaced_nodes = bashparse.substitute_variables(nodes, var_list)
    unrolled_nodes = unroll.replacement_unroll(nodes, var_list = {})

    # Generate the templates from each sequence of nodes
    templates = generate_templates(nodes)
    templates += generate_templates(replaced_nodes)
    templates += generate_templates(unrolled_nodes)

    # Add the new templates to the records
    template_record = add_templates(templates, template_record)

    return template_record
