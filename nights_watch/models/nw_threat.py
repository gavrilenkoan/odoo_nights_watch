from odoo import api, fields, models


class NwThreat(models.Model):
    """Threat beyond the Wall a ranging can be sent against."""

    _name = 'nw.threat'
    _description = 'Threat Beyond the Wall'
    _order = 'first_seen desc, name'

    name = fields.Char(required=True)
    threat_type = fields.Selection(
        selection=[
            ('wildling', 'Wildlings'),
            ('white_walker', 'White Walkers'),
            ('giant', 'Giants'),
            ('deserter', 'Deserters'),
            ('other', 'Other'),
        ],
        default='other',
        required=True,
    )
    severity = fields.Selection(
        selection=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('existential', 'Existential'),
        ],
        default='medium',
        required=True,
    )
    region = fields.Char(help='Where the threat was spotted.')
    first_seen = fields.Date(default=fields.Date.context_today)
    is_active = fields.Boolean(string='Still Active', default=True)
    description = fields.Text(translate=True)

    ranging_ids = fields.One2many(
        comodel_name='nw.ranging',
        inverse_name='threat_id',
        string='Rangings',
    )
    ranging_count = fields.Integer(compute='_compute_ranging_count', store=True)

    @api.depends('ranging_ids')
    def _compute_ranging_count(self):
        """Count the rangings targeting this threat."""
        for threat in self:
            threat.ranging_count = len(threat.ranging_ids)
