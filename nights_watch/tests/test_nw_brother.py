from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import NightsWatchCase


@tagged('post_install', '-at_install')
class TestNwBrother(NightsWatchCase):
    """The life of a brother: the oath, an order, an office, and the end of it."""

    def test_the_road_from_recruit_to_the_headsman(self):
        """The whole status machine, and the one act it refuses on the way.

        A recruit says the words and joins the queue; an officer posts him to
        an order; an oathbreaker is struck from the rolls. The sword waits for
        a deserter and for no one else.
        """
        brother = self._brother('Rast of the Test Keep', status='recruit', order_id=False)

        brother.action_say_the_words()
        self.assertEqual(brother.status, 'waiting')
        self.assertTrue(brother.oath_date)

        brother.action_assign_order(self.stewards)
        self.assertEqual(brother.status, 'sworn')
        self.assertEqual(brother.order_id, self.stewards)

        with self.assertRaises(UserError), self.env.cr.savepoint():
            brother.action_execute()

        brother.action_desert()
        brother.action_execute()
        self.assertEqual(brother.status, 'executed')
        self.assertFalse(brother.in_service)

    def test_appointing_a_man_unseats_his_predecessor(self):
        """A castle-wide office passes over rather than being refused, and a
        man who leaves the rolls frees it for the next."""
        old = self._brother('Benjen of the Test Keep', role_id=self.role_first_ranger.id)
        new = self._brother('Jeremy of the Test Keep', role_id=self.role_first_ranger.id)

        self.assertFalse(old.role_id)
        self.assertEqual(new.role_id, self.role_first_ranger)

        new.action_declare_fallen()
        third = self._brother('Dywen of the Test Keep', role_id=self.role_first_ranger.id)

        self.assertEqual(third.role_id, self.role_first_ranger)

    def test_the_chain_of_command_is_derived_and_has_no_cycles(self):
        """Recruits answer to the master-at-arms, rangers to the First of
        their order, the Firsts to their commander, and the commander to no
        one on the Wall."""
        commander = self._commander('Jeor of the Test Keep')
        instructor = self._brother(
            'Alliser of the Test Keep', role_id=self.role_instructor.id,
        )
        first = self._brother('Jeremy of the Test Keep', role_id=self.role_first_ranger.id)
        ranger = self._brother('Grenn of the Test Keep')
        recruit = self._brother('Pypar of the Test Keep', status='recruit', order_id=False)

        self.assertFalse(commander.mentor_id)
        self.assertEqual(first.mentor_id, commander)
        self.assertEqual(ranger.mentor_id, first)
        self.assertEqual(recruit.mentor_id, instructor)

        for brother in commander | instructor | first | ranger | recruit:
            self.assertNotEqual(brother.mentor_id, brother)
