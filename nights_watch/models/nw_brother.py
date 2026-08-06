from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

SERVING_STATUSES = ('recruit', 'waiting', 'sworn', 'ranging')


class NwBrother(models.Model):
    """Recruit or sworn brother of the Night's Watch.

    Holds the extended brother card: identity, service, background story,
    personal traits and the rangings he took part in.
    """

    _name = 'nw.brother'
    _description = "Brother of the Night's Watch"
    _order = 'seniority desc, name'

    name = fields.Char(required=True, index=True)
    nickname = fields.Char(help='Name he is known by on the Wall.')
    image = fields.Image(string='Portrait', max_width=1920, max_height=1920)
    image_128 = fields.Image(
        string='Portrait (128)',
        related='image',
        max_width=128,
        max_height=128,
        store=True,
    )
    birth_date = fields.Date()
    age = fields.Integer(compute='_compute_age')
    origin = fields.Char(string='Comes From', help='Region or house he was born in.')

    status = fields.Selection(
        selection=[
            ('recruit', 'Recruit'),
            ('waiting', 'Awaiting Assignment'),
            ('sworn', 'Sworn'),
            ('ranging', 'Ranging'),
            ('lost', 'Lost Beyond the Wall'),
            ('refused', 'Refused the Oath'),
            ('deserted', 'Deserted'),
            ('executed', 'Executed'),
            ('fallen', 'Fallen'),
        ],
        default='recruit',
        required=True,
    )
    in_service = fields.Boolean(
        compute='_compute_in_service',
        store=True,
        help='Still on the rolls. A brother lost beyond the Wall, fallen or '
        'deserted holds no office: his post passes to another man.',
    )
    order_id = fields.Many2one(
        comodel_name='nw.order',
        string='Order',
        help='Empty until the recruit says the words.',
    )
    role_id = fields.Many2one(
        comodel_name='nw.role',
        string='Office',
        help='Personal appointment on top of the order: castle commander, maester, septon, master-at-arms, recruiter.',
    )
    role_outside_orders = fields.Boolean(
        related='role_id.outside_orders',
        readonly=True,
    )
    seniority = fields.Integer(
        related='role_id.seniority',
        store=True,
        readonly=True,
    )
    standing = fields.Selection(
        selection=[
            ('rangers', 'Rangers'),
            ('builders', 'Builders'),
            ('stewards', 'Stewards'),
            ('outside', 'Outside the Orders'),
            ('waiting', 'Awaiting Assignment'),
            ('recruit', 'Recruits'),
        ],
        compute='_compute_standing',
        store=True,
        group_expand=True,
        help='Where a brother stands relative to the three orders: a man of '
        'an order, an office above them all, or a recruit who has joined '
        'none of them yet.',
    )
    castle_id = fields.Many2one(comodel_name='nw.castle', string='Castle')
    oath_date = fields.Date(string='Date of the Oath')
    years_of_service = fields.Integer(compute='_compute_years_of_service')

    mentor_id = fields.Many2one(
        comodel_name='nw.brother',
        string='Mentor',
        compute='_compute_mentor_id',
        store=True,
        help='Recruits answer to the master-at-arms, sworn brothers to the '
        'First of their order, the Firsts to the commander of their '
        'castle. The commander answers to no one on the Wall.',
    )

    is_steward = fields.Boolean(compute='_compute_is_steward', store=True)
    is_senior = fields.Boolean(
        compute='_compute_is_senior',
        store=True,
        help='May be assigned a personal steward.',
    )
    serves_id = fields.Many2one(
        comodel_name='nw.brother',
        string='Serves',
        help='A steward is assigned to a senior brother he serves.',
    )
    steward_ids = fields.One2many(
        comodel_name='nw.brother',
        inverse_name='serves_id',
        string='Personal Stewards',
    )

    recruitment_reason = fields.Selection(
        selection=[
            ('volunteer', 'Volunteer'),
            ('crime', 'Sentenced for a Crime'),
            ('bastard', 'Bastard Born'),
            ('exile', 'Exiled'),
            ('orphan', 'Orphan'),
            ('debt', 'Debt'),
            ('political', 'Political Reasons'),
        ],
        help='Why he ended up on the Wall.',
    )
    former_life = fields.Char(help='What he was before the Wall: smith, lord, thief...')
    is_wildling = fields.Boolean(string='Former Wildling')
    is_noble_born = fields.Boolean(string='Noble Born')

    skills = fields.Char(help='Sword, bow, healing, scouting, letters...')
    weapon = fields.Char()
    is_warg = fields.Boolean(string='Warg')
    can_read = fields.Boolean(string='Literate')
    notable_deed = fields.Text()

    user_id = fields.Many2one(comodel_name='res.users', string='System User')
    ranging_ids = fields.Many2many(
        comodel_name='nw.ranging',
        relation='nw_ranging_brother_rel',
        column1='brother_id',
        column2='ranging_id',
        string='Rangings',
    )
    ranging_count = fields.Integer(compute='_compute_ranging_count')
    active = fields.Boolean(default=True)

    _serves_not_self = models.Constraint(
        'CHECK (serves_id IS NULL OR serves_id != id)',
        'A brother cannot serve himself.',
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Relieve the sitting holder before the newcomer takes his office.

        :param vals_list: values of the brothers to create.
        :return: the created brothers.
        """
        for vals in vals_list:
            self._relieve_office(
                self.env['nw.role'].browse(vals.get('role_id')),
                vals.get('castle_id'),
            )

        return super().create(vals_list)

    def write(self, vals):
        """Refuse an unearned execution, and relieve a replaced office holder.

        :param vals: values to write.
        :return: True
        """
        if vals.get('status') == 'executed':
            self._check_execution()

        role = self.env['nw.role'].browse(vals.get('role_id'))
        if role:
            for brother in self:
                self._relieve_office(
                    role,
                    vals.get('castle_id') or brother.castle_id.id,
                    exclude=brother,
                )

        return super().write(vals)

    def _relieve_office(self, role, castle_id, exclude=None):
        """Take a limited office from whoever holds it.

        A castle answers to one commander and each order to one First per
        castle, so appointing a man necessarily unseats his predecessor.

        :param role: the office about to be handed over.
        :param castle_id: castle of the newcomer, for castle-wide offices.
        :param exclude: brother who must keep the office (the newcomer).
        :return: None
        """
        if not role or role.scope == 'free':
            return

        domain = [('role_id', '=', role.id)]

        if role.scope == 'castle':
            if not castle_id:
                return
            domain.append(('castle_id', '=', castle_id))

        if exclude:
            domain.append(('id', 'not in', exclude.ids))

        for holder in self.sudo().search(domain):
            values = {'role_id': False}

            if holder.in_service and not holder.order_id:
                values['status'] = 'waiting'

            holder.write(values)

    def _check_execution(self):
        """Refuse to execute a brother who never broke his oath.

        The Watch beheads deserters, and only deserters. A man still on the
        rolls, lost beyond the Wall or already dead cannot be put to the sword.

        :raises UserError: when a brother is not a deserter.
        """
        innocent = self.filtered(lambda brother: brother.status != 'deserted')
        if innocent:
            raise UserError(self.env._(
                'The Watch beheads deserters, and only deserters. '
                '%(names)s never broke his oath.',
                names=', '.join(innocent.mapped('name')),
            ))

    @api.depends('name', 'nickname')
    def _compute_display_name(self):
        """Show the nickname next to the name: ``Jon Snow ("Lord Snow")``."""
        for brother in self:
            if brother.nickname:
                brother.display_name = f'{brother.name} ("{brother.nickname}")'
            else:
                brother.display_name = brother.name

    @api.depends('birth_date')
    def _compute_age(self):
        """Full years between ``birth_date`` and today, 0 when unknown."""
        today = fields.Date.today()

        for brother in self:
            if not brother.birth_date:
                brother.age = 0
                continue

            age = today.year - brother.birth_date.year
            if (today.month, today.day) < (brother.birth_date.month, brother.birth_date.day):
                age -= 1

            brother.age = age

    @api.depends('oath_date')
    def _compute_years_of_service(self):
        """Full years served since the oath, 0 for a recruit."""
        today = fields.Date.today()

        for brother in self:
            if not brother.oath_date:
                brother.years_of_service = 0
                continue

            years = today.year - brother.oath_date.year
            if (today.month, today.day) < (brother.oath_date.month, brother.oath_date.day):
                years -= 1

            brother.years_of_service = max(years, 0)

    @api.depends('role_id.outside_orders', 'order_id.code', 'status')
    def _compute_standing(self):
        """Place every brother relative to the three orders.

        A maester, a septon or the commander of a castle stands above all
        three; every other sworn brother belongs to his own; a recruit has
        joined none of them yet.
        """
        for brother in self:
            if brother.role_id.outside_orders:
                brother.standing = 'outside'
            elif brother.order_id:
                brother.standing = brother.order_id.code
            elif brother.status == 'waiting':
                brother.standing = 'waiting'
            else:
                brother.standing = 'recruit'

    @api.depends('status')
    def _compute_in_service(self):
        """Flag the brothers still counted on the rolls of the Watch."""
        for brother in self:
            brother.in_service = brother.status in SERVING_STATUSES

    @api.depends('status', 'order_id', 'castle_id',
        'castle_id.instructor_id', 'castle_id.commander_id',
        'castle_id.brother_ids.role_id', 'castle_id.brother_ids.in_service',
    )
    def _compute_mentor_id(self):
        """Derive the chain of command inside a castle instead of typing it.

        A recruit is trained by the master-at-arms. A sworn brother answers
        to the First of his own order. The Firsts answer to the commander of
        the castle, and the commander answers to no one on the Wall.
        """
        for brother in self:
            if brother.status == 'recruit':
                mentor = brother.castle_id.instructor_id
            elif brother.status == 'waiting':
                mentor = brother.castle_id.commander_id
            elif brother.role_id.commands_castle:
                mentor = self.browse()
            elif brother.role_id.is_order_head:
                mentor = brother.castle_id.commander_id
            else:
                mentor = brother.castle_id.brother_ids.filtered(lambda holder: (
                    holder.in_service
                    and holder.role_id.is_order_head
                    and holder.role_id.order_id == brother.order_id
                ))[:1]

            brother.mentor_id = mentor if mentor != brother else False

    @api.depends('order_id.code')
    def _compute_is_steward(self):
        """Flag the brothers that belong to the order of Stewards."""
        for brother in self:
            brother.is_steward = brother.order_id.code == 'stewards'

    @api.depends('role_id.is_senior')
    def _compute_is_senior(self):
        """A brother is senior when the office he holds is a senior one."""
        for brother in self:
            brother.is_senior = brother.role_id.is_senior

    @api.depends('ranging_ids')
    def _compute_ranging_count(self):
        """Count the rangings the brother took part in."""
        for brother in self:
            brother.ranging_count = len(brother.ranging_ids)

    @api.constrains('serves_id', 'order_id')
    def _check_steward(self):
        """A personal steward is a steward, and he serves a senior brother.

        :raises ValidationError: when the server is not of the Stewards, or
            when the served brother holds no senior office.
        """
        for brother in self:
            if not brother.serves_id:
                continue

            if not brother.is_steward:
                raise ValidationError(self.env._(
                    'Only a brother of the Stewards may be assigned to serve '
                    'someone. %(name)s does not belong to that order.',
                    name=brother.name,
                ))

            if not brother.serves_id.is_senior:
                raise ValidationError(self.env._(
                    'A personal steward may only be assigned to a senior brother. '
                    '%(name)s holds no senior office.',
                    name=brother.serves_id.name,
                ))

    @api.constrains('role_id', 'castle_id', 'status')
    def _check_role_scope(self):
        """Enforce how many brothers may hold the same office at once.

        :raises ValidationError: when a recruit is given an office, when a
            castle-scoped office is given to a brother with no castle, or
            when the office is already taken within its scope.
        """
        for brother in self:
            role = brother.role_id
            if not role or not brother.in_service:
                continue

            if brother.status == 'recruit':
                raise ValidationError(self.env._(
                    'A recruit holds no office until he says the words.',
                ))

            if role.scope == 'free':
                continue

            domain = [
                ('role_id', '=', role.id),
                ('id', '!=', brother.id),
                ('in_service', '=', True),
            ]

            if role.scope == 'castle':
                if not brother.castle_id:
                    raise ValidationError(self.env._(
                        '"%(role)s" is an office of a castle, so %(name)s must '
                        'be quartered in one.',
                        role=role.name,
                        name=brother.name,
                    ))
                domain.append(('castle_id', '=', brother.castle_id.id))

            if self.sudo().search_count(domain, limit=1):
                raise ValidationError(self.env._(
                    '"%(role)s" is already held by another brother.',
                    role=role.name,
                ))

    @api.constrains('status', 'order_id', 'role_id')
    def _check_order(self):
        """Who belongs to an order, and who stands above them all.

        :raises ValidationError: when a recruit is already given an order,
            when an office that stands outside the orders is combined with
            one, or when a sworn brother belongs to no order at all.
        """
        for brother in self:
            if brother.role_id.outside_orders:
                if brother.order_id:
                    raise ValidationError(self.env._(
                        '"%(role)s" stands above the three orders, so %(name)s '
                        'belongs to none of them.',
                        role=brother.role_id.name,
                        name=brother.name,
                    ))
                continue

            if brother.status == 'recruit':
                if brother.order_id:
                    raise ValidationError(self.env._(
                        'A recruit joins an order only when he says the words.',
                    ))
                continue

            if brother.status == 'waiting':
                if brother.role_id:
                    raise ValidationError(self.env._(
                        '%(name)s is still awaiting an assignment, so he holds no office yet.',
                        name=brother.name,
                    ))

                if not brother.castle_id:
                    raise ValidationError(self.env._(
                        '%(name)s waits at a castle for its commander to post him. He has none.',
                        name=brother.name,
                    ))

                continue

            if brother.status in ('sworn', 'ranging') and not brother.order_id:
                raise ValidationError(self.env._(
                    'Every sworn brother belongs to an order. %(name)s has none.',
                    name=brother.name,
                ))

    @api.constrains('role_id', 'order_id')
    def _check_role_order(self):
        """An office tied to an order may only be held by its members.

        :raises ValidationError: when the holder belongs to another order.
        """
        for brother in self:
            role_order = brother.role_id.order_id
            if role_order and brother.order_id != role_order:
                raise ValidationError(self.env._(
                    '"%(role)s" is an office of the %(order)s, so %(name)s must '
                    'belong to that order.',
                    role=brother.role_id.name,
                    order=role_order.name,
                    name=brother.name,
                ))

    @api.constrains('role_id', 'castle_id', 'status')
    def _check_castle_commander(self):
        """A castle answers to one commander, whatever office he holds.

        :raises ValidationError: when a commanding office is given to a
            brother with no castle, or when the castle already has one.
        """
        for brother in self:
            if not brother.role_id.commands_castle or not brother.in_service:
                continue

            if not brother.castle_id:
                raise ValidationError(self.env._(
                    '"%(role)s" commands a castle, so %(name)s must be '
                    'quartered in one.',
                    role=brother.role_id.name,
                    name=brother.name,
                ))

            if self.sudo().search_count([
                ('id', '!=', brother.id),
                ('castle_id', '=', brother.castle_id.id),
                ('role_id.commands_castle', '=', True),
                ('in_service', '=', True),
            ], limit=1):
                raise ValidationError(self.env._(
                    '"%(castle)s" already answers to a commander.',
                    castle=brother.castle_id.name,
                ))

    def action_say_the_words(self, oath_date=None):
        """Take the oath. The man is of the Watch, but of no order yet.

        Which order he serves is not his to choose: he waits for the
        commander of his castle, or the First of an order, to post him.

        :param oath_date: date of the oath, today when omitted.
        :return: True
        :raises UserError: when the brother is not a recruit, or has no castle.
        """
        for brother in self:
            if brother.status != 'recruit':
                raise UserError(self.env._(
                    '%(name)s has already said the words.', name=brother.name,
                ))

            if not brother.castle_id:
                raise UserError(self.env._(
                    '%(name)s must be posted to a castle before the oath.',
                    name=brother.name,
                ))

        return self.write({
            'status': 'waiting',
            'oath_date': oath_date or fields.Date.context_today(self),
        })

    def action_assign_order(self, order=None):
        """Post a sworn brother who is awaiting assignment to an order.

        :param order: the ``nw.order`` to post them to, using the one already
            named on each record when omitted.
        :return: True
        :raises UserError: when a brother is not awaiting assignment, or when
            no order is named for him.
        """
        for brother in self:
            if brother.status != 'waiting':
                raise UserError(self.env._(
                    '%(name)s is not awaiting an assignment.', name=brother.name,
                ))

            if not (order or brother.order_id):
                raise UserError(self.env._(
                    'Name the order %(name)s is to serve in.', name=brother.name,
                ))

            brother.write({
                'status': 'sworn',
                'order_id': (order or brother.order_id).id,
            })

        return True

    def action_refuse(self):
        """Let a recruit turn back before he says the words.

        A man who never swore breaks no oath: he goes home, and the Watch has
        no claim on him. Once the words are said there is no going back. He is
        archived along the way: the Watch keeps the record, not the man.

        :return: True
        :raises UserError: when the brother has already said the words.
        """
        for brother in self:
            if brother.status != 'recruit':
                raise UserError(self.env._(
                    '%(name)s has already said the words. The Watch does not '
                    'release a sworn brother.',
                    name=brother.name,
                ))

        return self.write({'status': 'refused', 'active': False})

    def action_desert(self):
        """Strike an oathbreaker from the rolls.

        :return: True
        :raises UserError: when the brother is no longer in service.
        """
        for brother in self:
            if not brother.in_service:
                raise UserError(self.env._(
                    '%(name)s is no longer on the rolls of the Watch.',
                    name=brother.name,
                ))

        return self.write({'status': 'deserted'})

    def action_execute(self):
        """Carry out the sentence on a deserter.

        The refusal itself lives in :meth:`_check_execution`, which ``write``
        already calls.

        :return: True
        """
        return self.write({'status': 'executed'})

    def action_view_rangings(self):
        """Open the rangings this brother took part in.

        :return: an ``ir.actions.act_window`` dict.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Rangings'),
            'res_model': 'nw.ranging',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.ranging_ids.ids)],
        }

    def action_found(self):
        """A man given up for lost comes back through the gate.

        He returns to whatever duty he can still hold: to his order if he
        belongs to one, otherwise to the queue awaiting a posting. An office
        he held may have passed to another man while he was gone, and that is
        not undone by his return.

        :return: True
        :raises UserError: when the brother was not lost beyond the Wall.
        """
        for brother in self:
            if brother.status != 'lost':
                raise UserError(self.env._(
                    '%(name)s is not lost beyond the Wall.', name=brother.name,
                ))

            brother.write({
                'status': 'sworn' if brother.order_id else 'waiting',
            })

        return True

    def action_declare_dead(self):
        """Give up hope for a man lost beyond the Wall.

        :return: True
        :raises UserError: when the brother was not lost beyond the Wall.
        """
        for brother in self:
            if brother.status != 'lost':
                raise UserError(self.env._(
                    '%(name)s is not lost beyond the Wall.', name=brother.name,
                ))

        return self.write({'status': 'fallen'})
