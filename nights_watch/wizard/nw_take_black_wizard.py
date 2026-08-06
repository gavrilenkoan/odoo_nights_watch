from odoo import api, fields, models
from odoo.exceptions import UserError

RECRUITMENT_REASONS = [
    ('volunteer', 'Volunteer'),
    ('crime', 'Sentenced for a Crime'),
    ('bastard', 'Bastard Born'),
    ('exile', 'Exiled'),
    ('orphan', 'Orphan'),
    ('debt', 'Debt'),
    ('political', 'Political Reasons'),
]


class NwTakeBlackWizard(models.TransientModel):
    """Take the black: the choice a man makes for himself.

    The wizard asks the two things the rolls cannot guess — which castle he
    goes to train in, and what drove him to the Wall. Whose choice it is at
    all is settled by :meth:`~odoo.addons.nights_watch.models.res_partner.
    ResPartner._check_takes_the_black`.
    """

    _name = 'nw.take.black.wizard'
    _description = 'Take the Black'

    partner_ids = fields.Many2many(comodel_name='res.partner', string='Men')
    castle_id = fields.Many2one(
        comodel_name='nw.castle',
        string='Sent to',
        required=True,
        default=lambda self: self.env.user.nw_castle_id,
        help='A recruit trains under the master-at-arms of the castle he is sent to, '
             'and cannot say the words until he has one.',
    )
    recruitment_reason = fields.Selection(
        selection=RECRUITMENT_REASONS,
        string='Why He Came',
    )
    note = fields.Text(readonly=True)

    @api.model
    def default_get(self, fields_list):
        """Pick up the selected contacts, leaving out those we may not enlist.

        :param fields_list: fields whose default value is asked for.
        :return: the default values.
        """
        defaults = super().default_get(fields_list)

        if self.env.context.get('active_model') != 'res.partner':
            return defaults

        selected = self.env['res.partner'].browse(self.env.context.get('active_ids', [])).exists()
        fresh = selected.filtered(lambda partner: not partner.nw_recruit_brother_id)
        booked = fresh.filtered('user_ids')
        eligible = booked.filtered('nw_can_take_the_black')

        defaults['partner_ids'] = [fields.Command.set(eligible.ids)]

        notes = []
        if selected - fresh:
            notes.append(self.env._(
                'Already on the rolls of the Watch: %(names)s.',
                names=', '.join((selected - fresh).mapped('display_name')),
            ))
        if fresh - booked:
            notes.append(self.env._(
                'Keeps no book of his own, so the words could never be his to say: %(names)s.',
                names=', '.join((fresh - booked).mapped('display_name')),
            ))
        if booked - eligible:
            notes.append(self.env._(
                "No man takes the black in another man's place: %(names)s.",
                names=', '.join((booked - eligible).mapped('display_name')),
            ))
        defaults['note'] = '\n'.join(notes)

        return defaults

    def action_take_the_black(self):
        """Take the black for every man in the list and open the recruits.

        :return: an ``ir.actions.act_window`` dict listing the new recruits.
        :raises UserError: when no one is left to enlist.
        """
        self.ensure_one()

        if not self.partner_ids:
            raise UserError(self.env._('There is no one here to take the black.'))

        self.partner_ids._check_takes_the_black()

        for partner in self.partner_ids:
            partner.action_take_the_black(castle=self.castle_id, reason=self.recruitment_reason)

        recruits = self.partner_ids.nw_recruit_brother_id
        action = {
            'type': 'ir.actions.act_window',
            'name': self.env._('Recruits'),
            'res_model': 'nw.brother',
            'view_mode': 'list,form',
            'domain': [('id', 'in', recruits.ids)],
            'target': 'current',
        }

        if len(recruits) == 1:
            action.update({'view_mode': 'form', 'res_id': recruits.id, 'domain': []})

        return action
