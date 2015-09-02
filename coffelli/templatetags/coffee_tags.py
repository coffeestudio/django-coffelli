# coding: utf-8

from importlib import import_module
from django.template import TemplateSyntaxError
from django import template

#FIXME TMP TODO: Make sidebar extension for ModelAdmin
SITEMAP_MODEL = 'sitemap.models.Section'

register = template.Library()

# CoffeeStudio Admin Tags
@register.inclusion_tag("admin/includes_coffelli/sitemap.html")
def render_sitemap():
    if not SITEMAP_MODEL:
        return {'sitemap': None}
    module_name, class_name = SITEMAP_MODEL.rsplit('.', 1)
    module = import_module(module_name)
    instance = getattr(module, class_name)
    nodeset = instance.objects.all().order_by('level')
    # tree = build_tree(nodeset)
    return {'sitemap': nodeset}

class TraverseNode(template.Node):
    start_tag = 'traverse_mptt'
    end_tag = 'end_traverse_mptt'
    with_item_node = None
    descend_node = None
    context_var = None
    tpl = None

    def __init__(self, main_template, context_var, with_item_node, item_bind_to):
        self.tpl = main_template
        self.with_item_node = self.WithItemNode(with_item_node, item_bind_to)
        self.context_var = context_var

    def render(self, context):
        return self.render_tree(context, self.context_var.resolve(context))

    def render_tree(self, context, tree_data):
        out = [self.tpl[0].render(context)]
        lvl = 0
        for item in tree_data:
            if item.level > lvl:
                lvl = item.level
                out.append(self.tpl[0].render(context))
            elif item.level < lvl:
                lvl = item.level
                out.append(self.tpl[1].render(context))
            out.append(self.with_item_node.render(context, item, 0))
            out.append(self.with_item_node.render(context, item, 1))
        while True:
            out.append(self.tpl[1].render(context))
            lvl -= 1
            if lvl <= 0:
                break
        return "".join(out)

    class WithItemNode(template.Node):
        start_tag = 'with_item'
        end_tag = 'end_with_item'
        tpl = [None, None]
        bind = 'item'

        def __init__(self, node_template, bind):
            self.template = node_template
            self.bind = bind

        def render(self, context, item=None, mode=0):
            context[self.bind] = item
            return self.template[mode].render(context) if self.template[mode] else ''

    class DescendNode:
        start_tag = 'descend'
        end_tag = None

        def __init__(self):
            pass


@register.tag(name=TraverseNode.start_tag)
def compile_traverse_mptt(parser, token):
    def to_tag(p):
        return p[0], p[1:]

    states = {
        0: (TraverseNode.WithItemNode.start_tag, TraverseNode.end_tag),
        1: (TraverseNode.DescendNode.start_tag, TraverseNode.WithItemNode.end_tag)
    }
    state = 0
    tag, args = to_tag(token.split_contents())
    if len(args) < 1:
        raise TemplateSyntaxError("%s takes mptt result set parameter" % tag)
    context_var = template.Variable(args[0])
    main_mode = 0
    item_mode = 0
    main_template = [None, None]
    item_template = [None, None]
    item_bind = None
    while tag != TraverseNode.end_tag:
        nodes = parser.parse(states[state])
        if state == 0:
            if not main_template[main_mode]:
                main_template[main_mode] = nodes
            else:
                main_template[main_mode] += nodes
        elif state == 1:
            if not item_template[item_mode]:
                item_template[item_mode] = nodes
            else:
                item_template[item_mode] += nodes
        token = parser.next_token()
        tag, args = to_tag(token.split_contents())
        if state == 0 and tag == TraverseNode.WithItemNode.start_tag:
            state = 1
            if len(args) > 0:
                item_bind = args[0]
        elif state == 1:
            if tag == TraverseNode.WithItemNode.end_tag:
                state = 0
                main_mode = 1
            elif tag == TraverseNode.DescendNode.start_tag:
                item_mode = 1
    return TraverseNode(main_template, context_var, item_template, item_bind)
