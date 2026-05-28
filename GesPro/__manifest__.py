
{
    'name': 'GesPro - Appels à Concurrence',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Gestion complète des appels à concurrence',
    'description': '''
        Module de gestion des Appels à Concurrence pour IT Projet.
        Détection → Préparation → Soumission → Résultats
    ''',
    'author': 'IT Projet',
    'website': 'https://www.it-projet.com',
    
    # Modules Odoo nécessaires
    'depends': [
        'base',      # Utilisateurs, droits, séquences
        'mail',      # Chatter, notifications, emails
        'web',       # Interface web
        'board',     # Tableaux de bord
        'web_responsive',  # Responsive design pour mobile
    ],
    'assets': {
        'web.assets_backend': [
            'GesPro/static/src/scss/gespro_theme.scss',
            'GesPro/static/src/js/checklist_filters.js',
        ],
    },
   
    # Fichiers chargés à l'installation
   'data': [
    # Sécurité
    'security/groups.xml',
    'security/ir.model.access.csv',
    'security/record_rules.xml',

    # Données initiales
    'data/sequences.xml',
    'data/cron_alertes.xml',

    # Vues (TOUTES avant le menu)
    'views/annonce_views.xml',
    'views/appel_views.xml',
    'views/lot_views.xml',
    'views/personnel_line_views.xml',
    'views/material_line_views.xml',
    'views/payment_views.xml',
    'views/checklist_line_views.xml',
    'views/similar_contract_views.xml',
    'views/cv_personnel_views.xml',

    # Dashboards
    'views/dashboard_ceo.xml',
    'views/dashboard_pm.xml',
    'views/dashboard_resadmin.xml',
    'views/dashboard_tech.xml',
    'views/dashboard_fin.xml',

    # Menu EN DERNIER
    'views/menu.xml',

    

    # Wizard
    'wizard/ignore_wizard_views.xml',

    # Rapports
    'reports/ao_report.xml',
],
    
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}