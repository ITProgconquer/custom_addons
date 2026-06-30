{
    'name': 'Gestion des Congés',
    'version': '1.0',
    'category': 'Human Resources',
    'depends': ['base', 'mail', 'hr'],

    'assets': {
        'web.assets_backend': [
            'IT_conges/static/src/scss/leave_style.scss',
        ],
    },

    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'data/cron.xml',
        'data/mail_template.xml',
        'views/leave_policy_views.xml',
        'views/leave_account_views.xml',
        'views/leave_request_views.xml',
        # 'views/dashboard_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
}