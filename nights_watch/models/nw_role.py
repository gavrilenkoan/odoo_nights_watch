from odoo import api, fields, models
from odoo.exceptions import ValidationError


class NwRole(models.Model):
    """Office a brother of the Watch may hold, on top of his order.

    An order says what a brother does day to day — ranging, building or
    keeping the stores. A role is his personal appointment: the Lord
    Commander, the maester, the septon, the master-at-arms who trains the
    recruits, the recruiters who ride south for new men.
    """

    _name = 'nw.role'
    _description = "Night's Watch Role"
    _order = 'seniority desc, sequence, name'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(
        required=True,
        help='Technical identifier, e.g. "instructor".',
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    description = fields.Text(translate=True)

    seniority = fields.Integer(
        default=0,
        help='The higher the number, the higher the office stands in the Watch.',
    )
    is_senior = fields.Boolean(
        string='Senior Office',
        help='A brother holding this role may be assigned a personal steward.',
    )
    scope = fields.Selection(
        selection=[
            ('watch', 'One in the whole Watch'),
            ('castle', 'One per castle'),
            ('free', 'No limit'),
        ],
        default='free',
        required=True,
        help='How many brothers may hold this office at the same time.',
    )
    trains_recruits = fields.Boolean(
        string='Trains Recruits',
        help='The master-at-arms: recruits of his castle are trained by him.',
    )
    outside_orders = fields.Boolean(
        string='Stands Outside the Orders',
        help='The office places its holder above the three orders: he belongs '
             'to none of them. The Lord Commander, the maester, the septon.',
    )
    order_id = fields.Many2one(
        comodel_name='nw.order',
        string='Order',
        help='The office belongs to this order: only its members may hold it. '
             'Empty for offices open to a brother of any order.',
    )
    is_order_head = fields.Boolean(
        string='Heads the Order',
        help='The First of his order in his castle. The brothers of that order '
             'quartered with him answer to him.',
    )

    brother_ids = fields.One2many(
        comodel_name='nw.brother',
        inverse_name='role_id',
        string='Holders',
    )
    brother_count = fields.Integer(
        string='# Holders',
        compute='_compute_brother_count',
        store=True,
    )

    _code_uniq = models.Constraint(
        'UNIQUE (code)',
        'A role with this code already exists.',
    )

    @api.depends('brother_ids')
    def _compute_brother_count(self):
        """Count the brothers currently holding this office."""
        for role in self:
            role.brother_count = len(role.brother_ids)

    @api.constrains('is_order_head', 'order_id', 'scope')
    def _check_order_head(self):
        """A head-of-order office is tied to one order and to one castle.

        :raises ValidationError: when the office heads an order but names none,
            or when it is not limited to a single castle.
        """
        for role in self:
            if not role.is_order_head:
                continue

            if not role.order_id:
                raise ValidationError(self.env._(
                    '"%(role)s" heads an order, so it must name which one.',
                    role=role.name,
                ))

            if role.scope != 'castle':
                raise ValidationError(self.env._(
                    'Each castle has its own First, so "%(role)s" must be '
                    'limited to one per castle.',
                    role=role.name,
                ))
