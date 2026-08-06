from odoo.tests import tagged

from .common import NightsWatchCase


@tagged('post_install', '-at_install')
class TestNwThreat(NightsWatchCase):
    """Threats beyond the Wall and the rangings sent against them."""

    def test_rangings_against_a_threat_are_counted(self):
        """``ranging_count`` follows the parties sent against the threat."""
        before = self.threat.ranging_count

        self.Ranging.create({
            'name': 'Test Patrol Against the Free Folk',
            'castle_id': self.castle.id,
            'threat_id': self.threat.id,
        })
        self.threat.invalidate_recordset()

        self.assertEqual(self.threat.ranging_count, before + 1)

    def test_open_rangings_is_filtered_by_threat(self):
        """The stat button opens the rangings against this threat alone."""
        action = self.threat.action_view_rangings()

        self.assertEqual(action['res_model'], 'nw.ranging')
        self.assertIn(('threat_id', '=', self.threat.id), action['domain'])
