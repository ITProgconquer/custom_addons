
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
    'website': 'https://www.itprojet.com',
    
    # Modules Odoo nécessaires
    'depends': [
        'base',      # Utilisateurs, droits, séquences
        'mail',      # Chatter, notifications, emails
        'web',       # Interface web
        'board',     # Tableaux de bord
    ],
    
    # Fichiers chargés à l'installation
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/annonce_view.xml',
        'views/reponse_ceo.xml',
        'data/sequences.xml',


        # sprint 2
        # 'views/appel_views.xml',

        #sprint 3
        # 'views/checklist_views.xml',
        #'views/paiement_views.xml',
        #'data/checklist_templates.xml',

        # sprint 4
        # 'data/cron_alerte.xml',
        # 'data/mail_template.xml',

        #sprint 5
        # 'views/dashboard_views.xml',
        
       
        
    ],
    
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}