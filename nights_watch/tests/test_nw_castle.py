from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import NightsWatchCase


@tagged('post_install', '-at_install')
class TestNwCastle(NightsWatchCase):
    """A castle knows its garrison, its commander and its master-at-arms."""

    def test_commander_and_instructor_are_derived_from_the_offices(self):
        """Neither is typed in: both are read off the garrison's offices."""
        commander = self._commander('Jeor of the Test Keep')
        instructor = self._brother(
            'Alliser of the Test Keep', role_id=self.role_instructor.id,
        )
        self.castle.invalidate_recordset()

        self.assertEqual(self.castle.commander_id, commander)
        self.assertEqual(self.castle.instructor_id, instructor)
        self.assertEqual(self.castle.garrison, 2)

    def test_capacity_is_not_exceeded(self):
        """A castle refuses a garrison larger than it can hold."""
        self._brother('Grenn of the Test Keep')
        self._brother('Pypar of the Test Keep')

        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.castle.write({'capacity': 1})
