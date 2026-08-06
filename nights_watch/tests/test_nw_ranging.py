from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import NightsWatchCase


@tagged('post_install', '-at_install')
class TestNwRanging(NightsWatchCase):
    """Parties sent beyond the Wall, and what becomes of the men in them."""

    def setUp(self):
        super().setUp()

        self.leader = self._brother('Qhorin of the Test Keep')
        self.scout = self._brother('Stonesnake of the Test Keep')
        self.ranging = self.Ranging.create({
            'name': 'Test Ranging to the Skirling Pass',
            'castle_id': self.castle.id,
            'threat_id': self.threat.id,
            'leader_id': self.leader.id,
            'brother_ids': [(6, 0, (self.leader | self.scout).ids)],
            'date_start': '2026-01-10',
        })

    def test_departing_sends_every_man_beyond_the_wall(self):
        """The ranging rides out and its party rides with it."""
        self.ranging.action_depart()

        self.assertEqual(self.ranging.status, 'ongoing')
        self.assertEqual(set(self.ranging.brother_ids.mapped('status')), {'ranging'})

    def test_coming_home_counts_the_fallen_and_returns_the_rest(self):
        """The casualties are mourned; the others go back to their duty."""
        self.ranging.action_depart()
        self.ranging.write({'casualty_ids': [(6, 0, self.leader.ids)]})

        self.ranging.action_return()

        self.assertEqual(self.ranging.status, 'returned')
        self.assertEqual(self.leader.status, 'fallen')
        self.assertEqual(self.scout.status, 'sworn')
        self.assertTrue(self.ranging.date_end)

    def test_only_sworn_brothers_ride_and_only_with_their_own_leader(self):
        """Two rules that keep a party honest, both refused before departure."""
        stranger = self._brother('Ebben of the Test Keep')
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.ranging.write({'leader_id': stranger.id})

        recruit = self._brother('Cuger of the Test Keep', status='recruit', order_id=False)
        self.ranging.write({'brother_ids': [(4, recruit.id)]})

        with self.assertRaises(UserError), self.env.cr.savepoint():
            self.ranging.action_depart()
