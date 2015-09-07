# coding: utf-8

from importlib import import_module
from django.http import QueryDict
from django.template import TemplateSyntaxError
from django import template
from django.core.urlresolvers import reverse
from django.db.models.fields.related import ForeignKey
from django.contrib.admin import ModelAdmin
import inspect

register = template.Library()

@register.simple_tag()
def admin_url(item):
    return reverse("admin:%s_%s_change" % (item._meta.app_label, item._meta.model_name), args=(item.id,))

memo_section_relation = {}

@register.simple_tag()
def section_filter_url(model, section):
    if not (hasattr(model, '_meta') and hasattr(section, '_meta')):
        return ''
    model_name = model._meta.model_name
    ffield = None
    if not model_name in memo_section_relation:
        for f in model._meta.get_fields():
            if not isinstance(f, ForeignKey):
                continue
            if not isinstance(section, f.rel.to):
                continue
            f_obj_name = f.name
            f_id_name = f.get_path_info()[0].target_fields[0].name
            ffield = lambda s: {"%s__%s__exact" % (f_obj_name, f_id_name): getattr(s, f_id_name)}
            break
        memo_section_relation[model_name] = ffield
    else:
        ffield = memo_section_relation[model_name]
    base_url = reverse("admin:%s_%s_changelist" % (model._meta.app_label, model_name))
    qd = QueryDict('', mutable=True)
    qd.update(ffield(section))
    return base_url + '?' + qd.urlencode()

@register.inclusion_tag("admin/includes_coffelli/sitemap.html")
def sidebar(focus):
    sidebar_obj = get_sidebar_models()
    if not sidebar_obj.sitemap:
        return {'sitemap': None}
    node_set = sidebar_obj.sitemap.objects.all().order_by('level')
    return {'sitemap': node_set, 'focus': focus}

def get_sidebar_models():
    from django.contrib.admin.sites import site
    from coffelli import SidebarAdminMixin
    sbar = Sidebar
    for model, model_admin in site._registry.items():
        if not isinstance(model_admin, SidebarAdminMixin):
            continue
        if model_admin.sitemap:
            sbar.sitemap = model
        else:
            sbar.models.append(model)
    return sbar

class Sidebar(object):
    focus_model = None
    sitemap = None
    models = []

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

    class DescendNode(object):
        start_tag = 'descend'
        end_tag = None

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
    main_mode = 0  # main_template target
    item_mode = 0  # item_template target
    main_template = [None, None]  # before item / after item
    item_template = [None, None]  # before descend / after descend
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
        elif state == 1:  # Scan for subtags inside main traverse tag
            if tag == TraverseNode.WithItemNode.end_tag:
                state = 0
                main_mode = 1
            elif tag == TraverseNode.DescendNode.start_tag:
                item_mode = 1
    return TraverseNode(main_template, context_var, item_template, item_bind)
