{
    'name': 'Vicidial Iframe Integration',
    'version': '1.0',
    'depends': ['base', 'crm', 'web'],
    'author': 'Tejaswi Dev',
    'installable': True,
    'application': True,
    'data': [
        'security/ir.model.access.csv',
        'views/custom_iframe_view_copy.xml',
        'views/menu.xml',
        'data/crm_stage_data.xml',
    ],
'assets': {
    'web.assets_backend': [
        "vicidial/static/src/css/custom_modal.css",
        'vicidial/static/src/js/custom_iframe_autoload.js',
        "vicidial/static/src/js/services_icon_widget_copy.js",
        "vicidial/static/src/js/custom_footer.js",


    ],
},
}
