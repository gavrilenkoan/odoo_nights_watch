from odoo import api, fields, models


class ResUsers(models.Model):
    """Users linked to their brother record, used by the record rules."""

    _inherit = 'res.users'

    nw_brother_ids = fields.One2many(
        comodel_name='nw.brother',
        inverse_name='user_id',
        string='Watch Records',
    )
    nw_brother_id = fields.Many2one(
        comodel_name='nw.brother',
        string='Brother of the Watch',
        compute='_compute_nw_brother',
    )
    nw_castle_id = fields.Many2one(
        comodel_name='nw.castle',
        string='Castle',
        compute='_compute_nw_brother',
    )
    nw_order_id = fields.Many2one(
        comodel_name='nw.order',
        string='Order',
        compute='_compute_nw_brother',
    )

    @api.depends('nw_brother_ids.castle_id', 'nw_brother_ids.order_id')
    def _compute_nw_brother(self):
        """Expose the brother record linked to the user, and where he serves."""
        for user in self:
            brother = user.nw_brother_ids[:1]
            user.nw_brother_id = brother
            user.nw_castle_id = brother.castle_id
            user.nw_order_id = brother.order_id
