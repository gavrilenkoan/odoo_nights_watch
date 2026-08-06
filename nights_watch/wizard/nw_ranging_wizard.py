from odoo import api, fields, models
from odoo.exceptions import UserError


class NwRangingWizard(models.TransientModel):
    """Form a ranging party out of the brothers picked in the rolls."""

    _name = 'nw.ranging.wizard'
    _description = 'Form a Ranging Party'

    name = fields.Char(string='Ranging', required=True)
    brother_ids = fields.Many2many(
        comodel_name='nw.brother',
        string='Party',
        domain=[('status', '=', 'sworn')],
    )
    leader_id = fields.Many2one(comodel_name='nw.brother', string='Leader')
    castle_id = fields.Many2one(
        comodel_name='nw.castle',
        string='Departs From',
        required=True,
        default=lambda self: self.env.user.nw_castle_id,
    )
    threat_id = fields.Many2one(
        comodel_name='nw.threat',
        string='Target Threat',
        domain=[('is_active', '=', True)],
    )
    date_start = fields.Date(string='Departure', required=True, default=fields.Date.context_today)
    objective = fields.Text()
    depart_now = fields.Boolean(
        string='Ride at Once',
        help='Send the party beyond the Wall straight away, instead of leaving it planned.',
    )
    note = fields.Text(readonly=True)

    @api.model
    def default_get(self, fields_list):
        """Pick up the selected brothers, keeping only those who may ride.

        Only a sworn brother rides beyond the Wall, and only his own garrison
        is an officer's to send: a man of another castle is left out rather
        than passed on, since the record rules would refuse the write anyway.

        :param fields_list: fields whose default value is asked for.
        :return: the default values.
        """
        defaults = super().default_get(fields_list)

        if self.env.context.get('active_model') != 'nw.brother':
            return defaults

        selected = self.env['nw.brother'].browse(self.env.context.get('active_ids', [])).exists()
        sworn = selected.filtered(lambda brother: brother.status == 'sworn')
        eligible = self._of_own_castle(sworn)

        defaults['brother_ids'] = [fields.Command.set(eligible.ids)]

        notes = []
        if selected - sworn:
            notes.append(
                self.env._(
                    'Only sworn brothers ride beyond the Wall. These stay behind: %(names)s.',
                    names=', '.join((selected - sworn).mapped('name')),
                )
            )
        if sworn - eligible:
            notes.append(
                self.env._(
                    'Quartered in another castle, and not yours to send: %(names)s.',
                    names=', '.join((sworn - eligible).mapped('name')),
                )
            )
        defaults['note'] = '\n'.join(notes)

        return defaults

    @api.model
    def _of_own_castle(self, brothers):
        """Keep the brothers whose castle the user answers for.

        An officer with no record of his own on the Wall — the administrator —
        answers for every castle, and nothing is sifted out for him.

        :param brothers: the brothers to sift.
        :return: those quartered in the user's own castle.
        """
        castle = self.env.user.nw_castle_id
        if not castle:
            return brothers

        return brothers.filtered(lambda brother: brother.castle_id == castle)

    def action_form_party(self):
        """Raise the ranging and open it, sending it off at once if asked.

        :return: an ``ir.actions.act_window`` dict opening the new ranging.
        :raises UserError: when nobody was left to ride.
        """
        self.ensure_one()
        self.env['nw.brother']._check_officer()

        if not self.brother_ids:
            raise UserError(self.env._('A ranging needs at least one brother.'))

        outsiders = self.brother_ids - self._of_own_castle(self.brother_ids)
        if outsiders:
            raise UserError(self.env._(
                'A ranging is raised from the garrison of one castle. These men answer to another: %(names)s.',
                names=', '.join(outsiders.mapped('name')),
            ))

        ranging = self.env['nw.ranging'].create({
            'name': self.name,
            'brother_ids': [fields.Command.set(self.brother_ids.ids)],
            'leader_id': self.leader_id.id,
            'castle_id': self.castle_id.id,
            'threat_id': self.threat_id.id,
            'date_start': self.date_start,
            'objective': self.objective,
        })

        if self.depart_now:
            ranging.action_depart()

        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Ranging'),
            'res_model': 'nw.ranging',
            'res_id': ranging.id,
            'view_mode': 'form',
            'target': 'current',
        }
