from odoo.tests import tagged

from .common import NightsWatchCase


@tagged('post_install', '-at_install')
class TestNwOrder(NightsWatchCase):
    """The three orders and the men attached to them."""

    def test_members_are_counted(self):
        """``member_count`` follows the brothers serving in the order."""
        before = self.rangers.member_count

        self._brother('Todder of the Test Keep')
        self._brother('Mully of the Test Keep')
        self.rangers.invalidate_recordset()

        self.assertEqual(self.rangers.member_count, before + 2)

    def test_firsts_are_listed_only_while_they_serve(self):
        """A First leaves the roll of Firsts the day he leaves the rolls."""
        first = self._brother('Denys of the Test Keep', role_id=self.role_first_ranger.id)

        self.assertIn(first, self.rangers.head_ids)

        first.action_declare_fallen()
        self.rangers.invalidate_recordset()

        self.assertNotIn(first, self.rangers.head_ids)
