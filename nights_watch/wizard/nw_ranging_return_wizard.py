from odoo import fields, models


class NwRangingReturnWizard(models.TransientModel):
    """Close a ranging: count the fallen, then bring the rest home.

    The casualties have to be named before the ranging is closed, not after:
    ``action_return`` reads them to decide who goes back to duty and who is
    counted among the fallen.
    """

    _name = 'nw.ranging.return.wizard'
    _description = 'Bring a Ranging Home'

    ranging_id = fields.Many2one(
        comodel_name='nw.ranging',
        string='Ranging',
        required=True,
        readonly=True,
        default=lambda self: self.env.context.get('active_id'),
    )
    party_ids = fields.Many2many(
        comodel_name='nw.brother',
        related='ranging_id.brother_ids',
        string='Party',
    )
    outcome = fields.Selection(
        selection=[
            ('returned', 'The Party Came Back'),
            ('lost', 'The Party Never Came Back'),
        ],
        default='returned',
        required=True,
        help='Those not counted among the casualties go back to their duty, '
             'or are given up as lost beyond the Wall.',
    )
    casualty_ids = fields.Many2many(
        comodel_name='nw.brother',
        relation='nw_ranging_return_casualty_rel',
        column1='wizard_id',
        column2='brother_id',
        string='Casualties',
    )
    date_end = fields.Date(string='Return', required=True, default=fields.Date.context_today)
    summary = fields.Html(string='Report')

    def action_confirm(self):
        """Write down what happened, then close the ranging.

        :return: an ``ir.actions.act_window_close`` dict.
        """
        self.ensure_one()
        self.env['nw.brother']._check_officer()

        self.ranging_id.write({
            'date_end': self.date_end,
            'summary': self.summary,
            'casualty_ids': [fields.Command.set(self.casualty_ids.ids)],
        })

        if self.outcome == 'returned':
            self.ranging_id.action_return()
        else:
            self.ranging_id.action_mark_lost()

        return {'type': 'ir.actions.act_window_close'}
