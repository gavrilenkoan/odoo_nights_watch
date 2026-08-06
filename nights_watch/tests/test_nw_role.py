from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import NightsWatchCase


@tagged('post_install', '-at_install')
class TestNwRole(NightsWatchCase):
    """Offices of the Watch: what an office may claim about itself."""

    def test_head_of_order_must_name_its_order(self):
        """An office that heads an order has to say which one."""
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.env['nw.role'].create({
                'name': 'First of Nothing',
                'code': 'first_nothing',
                'scope': 'castle',
                'is_order_head': True,
            })

    def test_holders_are_counted(self):
        """``brother_count`` follows the men actually holding the office."""
        before = self.role_recruiter.brother_count

        self._brother('Yoren of the Test Keep', role_id=self.role_recruiter.id)
        self._brother('Conwy of the Test Keep', role_id=self.role_recruiter.id)
        self.role_recruiter.invalidate_recordset()

        self.assertEqual(self.role_recruiter.brother_count, before + 2)
