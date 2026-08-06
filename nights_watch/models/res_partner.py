from odoo import api, fields, models
from odoo.exceptions import UserError


class ResPartner(models.Model):
    """Contacts extended with the choice to take the black."""

    _inherit = 'res.partner'

    nw_recruit_brother_id = fields.Many2one(
        comodel_name='nw.brother',
        string='Brother Record',
        readonly=True,
        copy=False,
        help='The record opened on the Wall the day this man took the black.',
    )
    nw_can_take_the_black = fields.Boolean(
        compute='_compute_nw_can_take_the_black',
        help='A man takes the black himself, and no one takes it for him, and '
        'he keeps a book of his own so the words are his to say. The Lord '
        'Commander keeps the rolls, and may enter a man who walked up to '
        'the gate on his own.',
    )

    @api.depends('nw_recruit_brother_id', 'user_ids')
    @api.depends_context('uid')
    def _compute_nw_can_take_the_black(self):
        """Whose choice it is to take the black, and whose it is not."""
        keeps_the_rolls = self.env.user.has_group('base.group_system')

        for partner in self:
            partner.nw_can_take_the_black = bool(
                partner.user_ids
                and not partner.nw_recruit_brother_id
                and (keeps_the_rolls or partner == self.env.user.partner_id)
            )

    def _check_takes_the_black(self):
        """Refuse to send another man to the Wall.

        No lord sends his son through this book and no officer enlists a man
        who never asked: the black is taken, not given. The Lord Commander
        keeps the rolls, and may enter a man who came to the gate himself.

        :raises UserError: when the contact is not the user's own.
        """
        for partner in self:
            if not partner.user_ids:
                raise UserError(self.env._(
                    '%(name)s keeps no book of his own. Give him a login before '
                    'he takes the black, for the words are his to say.',
                    name=partner.display_name,
                ))

        if self.env.su or self.env.user.has_group('base.group_system'):
            return

        for partner in self:
            if partner != self.env.user.partner_id:
                raise UserError(self.env._(
                    'No man takes the black in another man\'s place. This is '
                    '%(name)s to choose, and no one else.',
                    name=partner.display_name,
                ))

    def action_take_the_black(self, castle=None, reason=None):
        """Enlist a contact into the Watch as a recruit.

        A man who takes the black is a recruit and nothing else: he joins no
        order until he has said the words and been posted. He is written to
        the rolls with ``sudo``, since the guard has already settled that the
        choice is his, while the rolls themselves are an officer's to keep.

        His login follows him onto the rolls, so that the words of the oath
        are his to say and no one else's, and the groups of the Watch are
        handed to him the moment he is written down.

        :param castle: the ``nw.castle`` he is sent to train in.
        :param reason: why he ended up on the Wall.
        :return: an ``ir.actions.act_window`` dict opening the new brother.
        :raises UserError: when the contact already took the black.
        """
        self.ensure_one()
        self._check_takes_the_black()

        if self.nw_recruit_brother_id:
            raise UserError(self.env._(
                '%(name)s has already taken the black.',
                name=self.display_name,
            ))

        brother = self.env['nw.brother'].sudo().create({
            'name': self.name,
            'status': 'recruit',
            'origin': self.city or self.country_id.name,
            'castle_id': castle.id if castle else False,
            'recruitment_reason': reason,
            'user_id': self.user_ids[:1].id,
        })
        brother._sync_user_groups()
        self.sudo().write({'nw_recruit_brother_id': brother.id})

        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Brother'),
            'res_model': 'nw.brother',
            'res_id': brother.id,
            'view_mode': 'form',
            'target': 'current',
        }
