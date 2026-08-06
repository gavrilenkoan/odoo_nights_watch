from odoo import api, fields, models
from odoo.exceptions import UserError


class NwAssignWizard(models.TransientModel):
    """Post brothers awaiting an assignment to one of the three orders.

    The act itself belongs to :meth:`~odoo.addons.nights_watch.models.
    nw_brother.NwBrother.action_assign_order`; the wizard only gathers what
    the officer chose and hands it over in one go.
    """

    _name = 'nw.assign.wizard'
    _description = 'Post Brothers to an Order'

    brother_ids = fields.Many2many(
        comodel_name='nw.brother',
        string='Brothers',
        domain=[('status', '=', 'waiting')],
    )
    order_id = fields.Many2one(
        comodel_name='nw.order',
        string='Order',
        required=True,
    )
    role_id = fields.Many2one(
        comodel_name='nw.role',
        string='Office',
        help='Hand him an office along with his order. One man at a time: '
             'an office is held by one brother.',
    )
    single_brother = fields.Boolean(compute='_compute_single_brother')
    note = fields.Text(
        readonly=True,
        help='Who was dropped from the selection, and why.',
    )

    @api.model
    def default_get(self, fields_list):
        """Pick up the selected brothers, keeping only those we may post.

        A man of another castle is left out rather than passed on: the record
        rules would refuse the write anyway, and an officer is better told who
        was dropped than shown a bare access error.

        :param fields_list: fields whose default value is asked for.
        :return: the default values.
        """
        defaults = super().default_get(fields_list)

        if self.env.context.get('active_model') != 'nw.brother':
            return defaults

        selected = self.env['nw.brother'].browse(self.env.context.get('active_ids', [])).exists()
        waiting = selected.filtered(lambda brother: brother.status == 'waiting')

        castle = self.env.user.nw_castle_id
        eligible = waiting.filtered(lambda brother: not castle or brother.castle_id == castle)

        defaults['brother_ids'] = [fields.Command.set(eligible.ids)]

        notes = []
        if selected - waiting:
            notes.append(self.env._(
                'Not awaiting an assignment: %(names)s.',
                names=', '.join((selected - waiting).mapped('name')),
            ))
        if waiting - eligible:
            notes.append(self.env._(
                'Quartered in another castle, and not yours to post: %(names)s.',
                names=', '.join((waiting - eligible).mapped('name')),
            ))
        defaults['note'] = '\n'.join(notes)

        return defaults

    @api.depends('brother_ids')
    def _compute_single_brother(self):
        """Flag the case where an office may be offered along with the order."""
        for wizard in self:
            wizard.single_brother = len(wizard.brother_ids) == 1

    @api.onchange('brother_ids')
    def _onchange_brother_ids(self):
        """Drop the office as soon as a second man joins the selection."""
        if len(self.brother_ids) != 1:
            self.role_id = False

    def action_assign(self):
        """Post every selected brother to the order, and close the dialog.

        The office is written after the order, never before: a brother still
        awaiting an assignment may hold none, and ``_check_order`` says so.

        :return: an ``ir.actions.act_window_close`` dict.
        :raises UserError: when no one is left in the selection.
        """
        self.ensure_one()

        if not self.brother_ids:
            raise UserError(self.env._('There is no one here to post to an order.'))

        self.brother_ids.action_assign_order(self.order_id)

        if self.role_id:
            self.brother_ids.write({'role_id': self.role_id.id})

        return {'type': 'ir.actions.act_window_close'}
