# coding=utf-8
"""
RST directives for kindoc
"""
__author__ = (u"Sebastien BARTHELEMY <barthelemy@crans.org>")
__copyright__ = u"Copyright (C) 2014 Sébastien Barthélémy"


import string
import sphinx
from docutils.parsers.rst.roles import set_classes

from docutils.parsers.rst import Directive, directives
from docutils.parsers.rst.states import normalize_name
from docutils import nodes

# we should output "math_block" nodes when using raw docutils, but 
# "displaymath" nodes when used from within sphinx, so let bind the class
# locally. (also see setup function below).
#
# Also note tha depending on sphinx/docutils and also on the specific method
# used to render the math (mathjax, mathjs, pngmath, mathml...), the subset
# of allowed latex environment might differ.
from docutils.nodes import math_block
use_sphinx = False
# use https://github.com/ros/urdfdom
from urdf_parser_py import urdf

mass = r"""
\text{{Mass}} = {}
"""

com = r"""
\text{{G(S)}}_{{(O, R)}} =
    \left[
        \begin{{matrix}}
            {0[0]}\\{0[1]}\\{0[2]}
        \end{{matrix}}
    \right]
"""

rotational_inertia = r"""
\left[I_G(S)\right]_R =
    \left[\begin{{matrix}}
        {0.ixx} & {0.ixy} & {0.ixz} \\
        {0.ixy} & {0.iyy} & {0.iyz} \\
        {0.ixz} & {0.iyz} & {0.izz}
    \end{{matrix}}
\right]
"""

# this function is inspired from
# https://bitbucket.org/birkenfeld/sphinx-contrib/src/2f386f8932accdeab49e897c609bea0eef3686e4/py_directive/sphinxcontrib/py_directive.py?at=default
# for examples generating math for both docutils and sphinx
def create_math_block(latex):
    if use_sphinx:
        node = math_block()
        node['nowrap'] = False
        node['label'] = None
        node['latex'] = latex
    else:
        node = math_block(text=latex)
    return node

class Links(Directive):

    option_spec = {'file': directives.unchanged_required}
    def run(self):
        #set_classes(self.options)
        r = urdf.Robot.from_xml_file(self.options['file'])
        _nodes = []
        for link in r.links:
            if not link.inertial or link.inertial.mass <= 0.01:
                # skip romeo eyes because inertia is 0
                #print("skipping " + link.name)
                # TODO: make an option
                continue
            # what follows is much inspired from  RSTState.new_subsection method
            # from docutils/parsers/rst/states.py
            section_node = nodes.section()
            title = link.name
            lineno = 0
            messages = []
            textnodes, title_messages = self.state.inline_text(title, lineno)
            titlenode = nodes.title(title, '', *textnodes)
            name = normalize_name(titlenode.astext())
            section_node['names'].append(name)
            section_node['ids'].append(name) #todo
            section_node += titlenode
            section_node += messages
            section_node += title_messages
            #self.document.note_implicit_target(section_node, section_node)
            #self.state.section(link.name, "", "+", lineno, messages)
            #assert(link.inertial.origin.rotation[0] == 0)
            inertia_node = math_block(text=rotational_inertia.format(
                    link.inertial.inertia))
            inertia_node['nowrap'] = False
            inertia_node['label'] = None
            inertia_node['latex'] = rotational_inertia.format(
                    link.inertial.inertia)
            _nodes += [section_node,
                      nodes.Text("hihi"),
                      create_math_block(mass.format(
                          link.inertial.mass)),
                      create_math_block(com.format(
                          link.inertial.origin.position)),
                      create_math_block(rotational_inertia.format(
                          link.inertial.inertia))]
        return _nodes

# docutils setup
directives.register_directive('kindoc_links', Links)

# sphinx setup
def setup(app):
    # override math_block definition
    import sys
    import sphinx.ext.mathbase
    sys.modules[__name__].use_sphinx = True
    sys.modules[__name__].math_block = sphinx.ext.mathbase.displaymath
    # register directive
    app.add_directive('kindoc_links', Links)
