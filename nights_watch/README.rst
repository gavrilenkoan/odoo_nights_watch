=============
Night's Watch
=============

Registry of the sworn brotherhood of the Wall: three orders, manned castles, an
extended brother card, the road from recruit to sworn brother, ranging parties
sent beyond the Wall and the threats they are sent against.

The module is built around one idea: **a brother is described by three
independent axes**, not by a single rank.

* his **order** — what he does day to day: ranging, building, keeping the stores;
* his **office** — a personal appointment on top of it: castle commander,
  maester, septon, master-at-arms, First of an order;
* his **standing** — where he is on the road: recruit, awaiting an assignment,
  sworn, ranging, or gone from the rolls.

Everything else is derived from those three. The chain of command, the commander
of a castle, the master-at-arms who trains its recruits — none of them is typed
in by hand.

Features
========

Models
------

* ``nw.order`` — the three orders of the Watch.
* ``nw.role`` — an office, with flags saying how many men may hold it, whether
  it commands a castle, trains recruits or stands outside the orders.
* ``nw.castle`` — a manned castle; its commander and master-at-arms are read off
  the offices held by its garrison.
* ``nw.brother`` — the extended card: identity, service, background, traits,
  portrait, and the rangings he took part in.
* ``nw.ranging`` — a party sent beyond the Wall, with its casualties and report.
* ``nw.threat`` — what a ranging is sent against.

Two standard models are extended: ``res.partner`` gains the choice to take the
black, and ``res.users`` exposes the brother record the access rules read.

Derived rules
-------------

* **An office passes over rather than clashing.** Appointing a man to a
  castle-wide office unseats whoever held it.
* **Leaving the rolls frees the office.** No separate act is needed: a man out of
  service holds nothing.
* **The chain of command is computed.** Recruits answer to the master-at-arms,
  sworn brothers to the First of their own order in their own castle, the Firsts
  to their commander, and the commander to no one on the Wall.
* **The Watch beheads deserters, and only deserters.**
* **The oath is personal.** No officer and no administrator says the words for
  another man.

Wizards
-------

* **Post to an Order** — one order for a whole queue of men awaiting assignment.
* **Form a Ranging Party** — turn a selection of sworn brothers into a ranging.
* **Bring the Ranging Home** — name the fallen *before* the ranging is closed,
  which is the only moment the answer can still be recorded.
* **Take the Black** — turn a contact into a recruit, with his castle and the
  reason he came.

Reports
-------

Two QWeb-PDF reports, both reachable from ⚙ Actions → Print:

* **Ranging Report** — the party, the fate of every man in it, the objective,
  what came of it, and the roll of the fallen.
* **Brother Dossier** — the card of one man plus the table of every ranging he
  rode.

Installation
============

The module depends on ``base``, ``web`` and ``contacts``, all of them standard.
Drop it into the addons path and install as usual::

    python odoo-bin -c odoo.conf -d <database> -i nights_watch --with-demo

Configuration
=============

The printed reports take the header from the company record. To see the sigil of
the Watch on them rather than the default placeholder, set the company name and
logo in **Settings → Users & Companies → Companies**.

No other configuration is required. Groups are never assigned by hand: they
follow the office a brother holds, and are kept in step automatically.

Usage
=====

The road a man travels through the module:

#. A contact **takes the black** and becomes a recruit at a castle.
#. He **says the words** himself — nobody may do it for him — and joins the
   queue awaiting an assignment.
#. An officer **posts him to an order**, and he is sworn.
#. He **rides beyond the Wall** with a ranging party.
#. The ranging is **brought home**: the fallen are counted, the rest go back to
   their duty.

Demo data
=========

Installing with demo data gives four castles, thirty-six brothers, four rangings
and nine logins. **The password of every demo user equals the login.**

=============  ===========================  ===================  ==========================
Login          Brother                      Castle               Groups
=============  ===========================  ===================  ==========================
``mormont``    Jeor Mormont                 Castle Black         Brother, Officer, Commander
``mallister``  Denys Mallister              The Shadow Tower     Brother, Officer, Commander
``rykker``     Jeremy Rykker                Castle Black         Brother, Officer
``dalbridge``  Dalbridge                    The Shadow Tower     Brother, Officer
``aemon``      Aemon Targaryen              Castle Black         Brother, Officer
``cellador``   Cellador                     Castle Black         Brother, Officer
``jon``        Jon Snow                     Castle Black         Brother
``rast``       Rast (recruit)               Castle Black         Brother
``jeren``      Jeren (recruit)              Castle Black         Brother
=============  ===========================  ===================  ==========================

Two commanders and two Firsts sit in **different** castles on purpose: that pair
is what shows the castle isolation working. The two recruits with logins of their
own are there because the oath can only be said by the man himself.

Security
========

Three groups, each implying the one before it:

* **Brother** — reads the rolls of the whole Wall and changes nothing.
* **Officer** — enrols and posts the men of his own castle, deletes nothing.
* **Castle Commander** — may strike out the records of his own castle.

Access rights give the ceiling, record rules cut it down to a man's own castle
through ``user.nw_brother_id.castle_id``, and the guards inside the actions
decide whose act it is at all. The administrator works through the
``base.group_system`` rows and is deliberately kept outside the groups of the
Watch: the castle rule would otherwise lock him out, since he has no brother
record of his own.

Testing
=======

The suite builds its own fixtures and passes on a database installed with or
without demo data::

    python odoo-bin -c odoo.conf -d <database> -i nights_watch --with-demo \
        --test-enable --test-tags /nights_watch --stop-after-init

Known issues
============

* A man counted among the fallen carries no date of death. For a ranging it can
  be read from the return date; for a death at a castle there is nowhere to take
  it from.
* An office taken from a man leaves no trace. A full history of appointments
  would need a model of its own.

Credits
=======

Author: gavrilenko_an

License: LGPL-3