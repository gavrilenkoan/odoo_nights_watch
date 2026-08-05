from odoo import api, fields, models
from odoo.exceptions import ValidationError


class NwOrder(models.Model):
    """Order of the Night's Watch: Rangers, Builders or Stewards.

    Each order is headed by a "First" (First Ranger, First Builder,
    First Steward) and groups the brothers serving in it.
    """

    _name = 'nw.order'
    _description = "Night's Watch Order"
    _order = 'sequence, name'

    name = fields.Char(required=True, translate=True)
    code = fields.Selection(
        selection=[
            ('rangers', 'Rangers'),
            ('builders', 'Builders'),
            ('stewards', 'Stewards'),
        ],
        required=True,
    )
    sequence = fields.Integer(default=10)
    description = fields.Text(
        translate=True,
        help='Duties the order is responsible for.',
    )

    head_ids = fields.One2many(
        comodel_name='nw.brother',
        inverse_name='order_id',
        string='Firsts',
        domain=[('role_id.is_order_head', '=', True)],
    )
    member_ids = fields.One2many(
        comodel_name='nw.brother',
        inverse_name='order_id',
        string='Members',
    )
    member_count = fields.Integer(
        string='# Members',
        compute='_compute_member_count',
        store=True,
    )

    _code_uniq = models.Constraint(
        'UNIQUE (code)',
        'An order with this code already exists.',
    )

    @api.depends('member_ids')
    def _compute_member_count(self):
        """Count the brothers currently attached to the order."""
        for order in self:
            order.member_count = len(order.member_ids)

    @api.constrains('first_id')
    def _check_first_belongs_to_order(self):
        """The First of an order must himself be a member of that order.

        :raises ValidationError: if ``first_id`` belongs to another order.
        """
        for order in self:
            if order.first_id and order.first_id.order_id != order:
                raise ValidationError(self.env._(
                    'The First of "%(order)s" must be a member of this very order.',
                    order=order.name,
                ))
