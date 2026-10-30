{
    'name': 'IT Contrats',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Gestion des contrats employés',
    'depends': ['base', 'mail', 'hr'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'views/hr_contract_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
}