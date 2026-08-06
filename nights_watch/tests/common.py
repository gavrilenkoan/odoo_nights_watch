from odoo.tests.common import TransactionCase


class NightsWatchCase(TransactionCase):
    """Fixtures shared by every test of the Watch.

    Orders, roles and threats ship in ``data/`` and are therefore always
    installed; castles and brothers are built here rather than taken from
    ``demo/``, so the suite passes on a database installed without demo data.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.Brother = cls.env['nw.brother']
        cls.Ranging = cls.env['nw.ranging']

        cls.rangers = cls.env.ref('nights_watch.order_rangers')
        cls.stewards = cls.env.ref('nights_watch.order_stewards')

        cls.role_commander = cls.env.ref('nights_watch.role_commander')
        cls.role_first_ranger = cls.env.ref('nights_watch.role_first_ranger')
        cls.role_instructor = cls.env.ref('nights_watch.role_instructor')
        cls.role_recruiter = cls.env.ref('nights_watch.role_recruiter')

        cls.threat = cls.env.ref('nights_watch.threat_free_folk')

        cls.castle = cls.env['nw.castle'].create({'name': 'Test Keep'})

    @classmethod
    def _brother(cls, name, **values):
        """Create a sworn ranger of the test castle, overridden as needed.

        :param name: name of the brother.
        :param values: values overriding the defaults.
        :return: the created ``nw.brother``.
        """
        return cls.Brother.create({
            'name': name,
            'status': 'sworn',
            'order_id': cls.rangers.id,
            'castle_id': cls.castle.id,
            **values,
        })

    @classmethod
    def _commander(cls, name):
        """Appoint the commander of the test castle.

        The office stands outside the three orders, so its holder belongs to
        none of them.

        :param name: name of the brother.
        :return: the created ``nw.brother``.
        """
        return cls.Brother.create({
            'name': name,
            'status': 'sworn',
            'castle_id': cls.castle.id,
            'role_id': cls.role_commander.id,
        })
