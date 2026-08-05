# noinspection PyStatementEffect
{
    'name': "Night's Watch",
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'summary': "Orders, castles, brothers, rangings and threats of the Night's Watch",
    'description': """
Night's Watch
=============
Registry of the sworn brotherhood of the Wall: three orders, three manned
castles, an extended brother card, recruit assignment, personal stewards and
ranging parties sent beyond the Wall.
""",
    'author': 'gavrilenko_an',
    'website': 'https://github.com/gavrilenkoan/odoo_nights_watch',
    'license': 'LGPL-3',
    'application': True,

    'images': [
        'static/description/icon.png',
    ],

    'depends': [
        'base',
        'web',
    ],

    'data': [
        'security/ir.model.access.csv',

        'views/nights_watch_menu.xml',
        'views/nw_brother_views.xml',
        'views/nw_order_views.xml',
        'views/nw_castle_views.xml',
        'views/nw_role_views.xml',
        'views/nw_ranging_views.xml',
        'views/nw_threat_views.xml',
        'views/res_partner_views.xml',
        'views/res_users_views.xml',
    ],

    'installable': True,
    'auto_install': False,
}
