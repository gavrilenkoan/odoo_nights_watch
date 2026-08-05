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

    'depends': [
        'base',
        'web',
    ],

    'data': [
        'security/ir.model.access.csv',
    ],

    'installable': True,
    'auto_install': False,
}
