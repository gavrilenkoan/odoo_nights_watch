from odoo import api, fields, models
from odoo.exceptions import ValidationError


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
            ('sworn', 'Sworn'),
            ('ranging', 'Beyond the Wall'),
            ('deserted', 'Deserted'),
            ('fallen', 'Fallen'),
        ],
        default='recruit',
        required=True,
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

    @api.depends('status', 'order_id', 'castle_id',
                 'castle_id.instructor_id', 'castle_id.commander_id',
                 'castle_id.brother_ids.role_id')
    def _compute_mentor_id(self):
        """Derive the chain of command inside a castle instead of typing it.

        A recruit is trained by the master-at-arms. A sworn brother answers
        to the First of his own order. The Firsts answer to the commander of
        the castle, and the commander answers to no one on the Wall.
        """
        for brother in self:
            if brother.status == 'recruit':
                mentor = brother.castle_id.instructor_id
            elif brother.role_id.commands_castle:
                mentor = self.browse()
            elif brother.role_id.is_order_head:
                mentor = brother.castle_id.commander_id
            else:
                mentor = brother.castle_id.brother_ids.filtered(
                    lambda holder: holder.role_id.is_order_head
                    and holder.role_id.order_id == brother.order_id
                )[:1]

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
            if not role:
                continue

            if brother.status == 'recruit':
                raise ValidationError(self.env._(
                    'A recruit holds no office until he says the words.',
                ))

            if role.scope == 'free':
                continue

            domain = [('role_id', '=', role.id), ('id', '!=', brother.id)]

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

    @api.constrains('role_id', 'castle_id')
    def _check_castle_commander(self):
        """A castle answers to one commander, whatever office he holds.

        :raises ValidationError: when a commanding office is given to a
            brother with no castle, or when the castle already has one.
        """
        for brother in self:
            if not brother.role_id.commands_castle:
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
            ], limit=1):
                raise ValidationError(self.env._(
                    '"%(castle)s" already answers to a commander.',
                    castle=brother.castle_id.name,
                ))
