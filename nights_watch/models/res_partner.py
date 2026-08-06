from odoo import fields, models
from odoo.exceptions import UserError


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

    def action_take_the_black(self):
        """Enlist a contact into the Watch as a recruit.

        The intended order stays on the contact: a recruit joins no order
        until he has said the words and been posted.

        :return: an ``ir.actions.act_window`` dict opening the new brother.
        :raises UserError: when the contact already took the black.
        """
        self.ensure_one()

        if self.nw_recruit_brother_id:
            raise UserError(self.env._(
                '%(name)s has already taken the black.', name=self.display_name,
            ))

        brother = self.env['nw.brother'].create({
            'name': self.name,
            'status': 'recruit',
            'origin': self.city or self.country_id.name,
        })
        self.write({
            'is_nw_recruit': True,
            'nw_recruit_brother_id': brother.id,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Brother'),
            'res_model': 'nw.brother',
            'res_id': brother.id,
            'view_mode': 'form',
            'target': 'current',
        }
