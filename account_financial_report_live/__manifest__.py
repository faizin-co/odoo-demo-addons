{
    "name": "Financial Reports (Consistech)",
    "version": "18.0.1.0.0",
    "category": "Accounting",
    "summary": "Interactive on-screen financial reports using OCA engine (Consistech Viewer)",

    "author": "Consistech Solution",
    "website": "https://consistechsolution.com",
    "support": "support@consistechsolution.com",

    "depends": [
        "web",
        "account",
        "account_financial_report",   # OCA module (engine)
    ],

    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/actions.xml",
        "views/menu.xml",
        "report/report.xml",
    ],

    "assets": {
        "web.assets_backend": [
            "account_financial_report_live/static/src/js/report_service.js",
            "account_financial_report_live/static/src/js/report_action.js",
            "account_financial_report_live/static/src/xml/report_templates.xml",
        ],
    },

    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
