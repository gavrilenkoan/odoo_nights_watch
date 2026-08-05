from odoo import api, fields, models
from odoo.exceptions import ValidationError


class NwCastle(models.Model):
    """Manned castle on the Wall where the brothers are garrisoned."""

    _name = 'nw.castle'
    _description = 'Castle on the Wall'
    _order = 'sequence, name'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    region = fields.Char(help='Where on the Wall the castle stands.')
    description = fields.Text(translate=True)
    capacity = fields.Integer(help='Maximum garrison. 0 means unlimited.')
    is_active = fields.Boolean(
        string='Manned',
        default=True,
        help='Uncheck for an abandoned castle.',
    )

    commander_id = fields.Many2one(
        comodel_name='nw.brother',
        string='Commander',
        compute='_compute_commander_id',
        store=True,
        help='Commands this castle and answers for it to no one on the Wall.',
    )
    brother_ids = fields.One2many(
        comodel_name='nw.brother',
        inverse_name='castle_id',
        string='Brothers',
    )
    garrison = fields.Integer(
        compute='_compute_garrison',
        store=True,
        help='Number of brothers quartered in the castle.',
    )
    instructor_id = fields.Many2one(
        comodel_name='nw.brother',
        string='Master-at-arms',
        compute='_compute_instructor_id',
        store=True,
        help='Trains the recruits sent to this castle.',
    )
    recruit_ids = fields.One2many(
        comodel_name='nw.brother',
        inverse_name='castle_id',
        string='Recruits',
        domain=[('status', '=', 'recruit')],
    )
    head_ids = fields.One2many(
        comodel_name='nw.brother',
        inverse_name='castle_id',
        string='Order Firsts',
        domain=[('role_id.is_order_head', '=', True)],
    )

    _name_uniq = models.Constraint(
        'UNIQUE (name)',
        'A castle with this name already exists.',
    )

    @api.depends('brother_ids')
    def _compute_garrison(self):
        """Count the brothers quartered in the castle."""
        for castle in self:
            castle.garrison = len(castle.brother_ids)

    @api.depends('brother_ids.role_id.commands_castle')
    def _compute_commander_id(self):
        """The commander is whoever in the garrison holds a commanding office."""
        for castle in self:
            castle.commander_id = castle.brother_ids.filtered(
                lambda brother: brother.role_id.commands_castle
            )[:1]

    @api.depends('brother_ids.role_id.trains_recruits')
    def _compute_instructor_id(self):
        """The master-at-arms is whoever in the garrison holds a training office."""
        for castle in self:
            castle.instructor_id = castle.brother_ids.filtered(
                lambda brother: brother.role_id.trains_recruits
            )[:1]

    @api.constrains('brother_ids', 'capacity')
    def _check_capacity(self):
        """Refuse a garrison larger than the castle capacity.

        :raises ValidationError: when capacity is set and exceeded.
        """
        for castle in self:
            if castle.capacity and len(castle.brother_ids) > castle.capacity:
                raise ValidationError(self.env._(
                    '"%(castle)s" cannot hold more than %(capacity)s brothers.',
                    castle=castle.name,
                    capacity=castle.capacity,
                ))
