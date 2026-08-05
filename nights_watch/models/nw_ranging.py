from odoo import api, fields, models
from odoo.exceptions import ValidationError


class NwRanging(models.Model):
    """Ranging party sent beyond the Wall against a given threat."""

    _name = 'nw.ranging'
    _description = 'Ranging Beyond the Wall'
    _order = 'date_start desc, id desc'

    name = fields.Char(required=True)
    status = fields.Selection(
        selection=[
            ('planned', 'Planned'),
            ('ongoing', 'Beyond the Wall'),
            ('returned', 'Returned'),
            ('lost', 'Lost'),
        ],
        default='planned',
        required=True,
    )

    leader_id = fields.Many2one(comodel_name='nw.brother', string='Leader')
    brother_ids = fields.Many2many(
        comodel_name='nw.brother',
        relation='nw_ranging_brother_rel',
        column1='ranging_id',
        column2='brother_id',
        string='Party',
    )
    casualty_ids = fields.Many2many(
        comodel_name='nw.brother',
        relation='nw_ranging_casualty_rel',
        column1='ranging_id',
        column2='brother_id',
        string='Casualties',
    )

    castle_id = fields.Many2one(comodel_name='nw.castle', string='Departs From')
    threat_id = fields.Many2one(comodel_name='nw.threat', string='Target Threat')
    threat_type = fields.Selection(
        related='threat_id.threat_type',
        store=True,
        readonly=True,
    )

    date_start = fields.Date(default=fields.Date.context_today)
    date_end = fields.Date()
    duration = fields.Integer(
        compute='_compute_duration',
        store=True,
        help='Days spent beyond the Wall.',
    )

    member_count = fields.Integer(compute='_compute_counts', store=True)
    casualty_count = fields.Integer(compute='_compute_counts', store=True)

    objective = fields.Text()
    summary = fields.Html(string='Report')

    @api.depends('date_start', 'date_end')
    def _compute_duration(self):
        """Number of days between departure and return, 0 while away."""
        for ranging in self:
            if ranging.date_start and ranging.date_end:
                ranging.duration = (ranging.date_end - ranging.date_start).days
            else:
                ranging.duration = 0

    @api.depends('brother_ids', 'casualty_ids')
    def _compute_counts(self):
        """Size of the party and of the casualty list (graph measures)."""
        for ranging in self:
            ranging.member_count = len(ranging.brother_ids)
            ranging.casualty_count = len(ranging.casualty_ids)

    @api.constrains('leader_id', 'brother_ids')
    def _check_leader(self):
        """The leader must ride with his own party.

        :raises ValidationError: when the leader is outside ``brother_ids``.
        """
        for ranging in self:
            if ranging.leader_id and ranging.leader_id not in ranging.brother_ids:
                raise ValidationError(self.env._(
                    'The leader of "%(ranging)s" must be part of the ranging party.',
                    ranging=ranging.name,
                ))

    @api.constrains('casualty_ids', 'brother_ids')
    def _check_casualties(self):
        """Only members of the party can be listed as casualties.

        :raises ValidationError: when a casualty never left the Wall.
        """
        for ranging in self:
            strangers = ranging.casualty_ids - ranging.brother_ids
            if strangers:
                raise ValidationError(self.env._(
                    'These brothers were not part of "%(ranging)s": %(names)s.',
                    ranging=ranging.name,
                    names=', '.join(strangers.mapped('name')),
                ))

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        """Return date cannot precede the departure date.

        :raises ValidationError: on an inverted date range.
        """
        for ranging in self:
            if ranging.date_start and ranging.date_end and ranging.date_end < ranging.date_start:
                raise ValidationError(self.env._(
                    'A ranging cannot come back before it departs.',
                ))
