from django import template
from django.utils.html import format_html
from draw_menu.models import Tags

register = template.Library()


def get_from_db(url: str, menu_slug: str):
    query = '''
        WITH RECURSIVE cur_url AS (
            SELECT id AS cur_id
            FROM draw_menu_Tags
            WHERE url = %s
        ),
        cur_menu AS(
            SELECT id AS menu_id
            FROM draw_menu_Tags
            WHERE slug = %s
        ),
        parents AS (
            SELECT tags.*, 1 as trig
            FROM draw_menu_Tags AS tags, cur_url
            WHERE id = cur_id OR parent_id = cur_id

            UNION

            SELECT tags.*, MOD(trig + 1, 3)
            FROM draw_menu_Tags AS tags, parents
            WHERE (trig = 2 AND tags.id = parents.parent_id) OR
                  (trig = 1 AND tags.parent_id = parents.parent_id) OR
                  (trig = 0 AND tags.id = parents.id)
        )
        SELECT DISTINCT id, name, slug, url, parent_id
        FROM parents

        UNION

        SELECT id, name, slug, url, parent_id
        FROM draw_menu_Tags AS tags, cur_menu
        WHERE id = menu_id OR parent_id = menu_id
        ORDER BY id
        '''

    return Tags.objects.raw(query, [url, menu_slug])


def group_by_relation(node_list: list) -> dict:
    tree = {}
    for node in node_list:
        tree.setdefault(node, [])
        if not node.parent:
            tree['root'] = node
        else:
            parent = tree.setdefault(node.parent, [])
            parent.append(node)
    return tree


def tree_to_html(tree: dict, tag: Tags, cur_tag_mark: str,
                 lvl: int = 0, url: str = ''):
    if not tree:
        return ''
    html = tag.as_html(lvl=lvl, bold=True)
    nodes = tree[tag]
    for node in nodes:
        if tree[node] or node.url == cur_tag_mark:
            html += tree_to_html(tree, node, cur_tag_mark, lvl + 1)
        else:
            html += node.as_html(lvl=lvl + 1)
    return html


@register.simple_tag(takes_context=True)
def draw_menu(context, *args, ):
    menu_name = args[0]
    url = context['request'].path
    tags = get_from_db(url, menu_name)
    tree = group_by_relation(tags)
    html = ''
    if tree:
        root = tree['root']
        html = tree_to_html(tree, root, url)
    return format_html(html)
