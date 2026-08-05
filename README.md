# odoo_nights_watch

[![License: LGPL-3](https://img.shields.io/badge/licence-LGPL--3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0-standalone.html)
[![Odoo](https://img.shields.io/badge/Odoo-19.0-714B67.svg)](https://github.com/odoo/odoo/tree/19.0)

Odoo 19 Community addon — registry of the sworn brotherhood of the Wall.

Coursework project: three orders of the Night's Watch, the manned castles,
an extended brother card, the assignment of recruits after the oath, and the
ranging parties sent beyond the Wall against known threats.

## Modules

| Module | Version | Summary |
|--------|---------|---------|
| [`nights_watch`](nights_watch/) | 19.0.1.0.0 | Orders, castles, brothers, rangings and threats of the Night's Watch |

## Requirements

* Odoo 19.0 Community
* Python 3.10+
* PostgreSQL 12+

## Installation

Add this repository directory to your `addons_path`, then:
```commandline
odoo-bin -c odoo.conf -d <database> -i nights_watch --stop-after-init
```

## Tests
```commandline
odoo-bin -c odoo.conf -d <database> -u nights_watch
--test-enable --test-tags /nights_watch --stop-after-init
```


## License

LGPL-3 — see [LICENSE](LICENSE).

## Author

[gavrilenkoan](https://github.com/gavrilenkoan)
