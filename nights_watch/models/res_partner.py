from odoo import fields, models


class ResPartner(models.Model):
    """Contacts extended with Night's Watch recruitment data."""

    _inherit = 'res.partner'

    is_nw_recruit = fields.Boolean(string="Night's Watch Recruit")
    nw_recruit_order_id = fields.Many2one(
        comodel_name='nw.order',
        string='Intended Order',
    )
    nw_recruit_brother_id = fields.Many2one(
        comodel_name='nw.brother',
        string='Brother Record',
        readonly=True,
        copy=False,
    )
