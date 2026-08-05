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
        compute='_compute_nw_brother_id',
    )
    nw_castle_id = fields.Many2one(related='nw_brother_id.castle_id', string='Castle')
    nw_order_id = fields.Many2one(related='nw_brother_id.order_id', string='Order')

    @api.depends('nw_brother_ids')
    def _compute_nw_brother_id(self):
        """Expose the first brother record linked to the user, if any."""
        for user in self:
            user.nw_brother_id = user.nw_brother_ids[:1]
