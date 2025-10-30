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
        "views/export_lead_wizard_view.xml",
        'data/crm_stage_data.xml',
    ],
'assets': {
    'web.assets_backend': [
        "vicidial/static/src/css/custom_modal.css",
        'vicidial/static/src/js/custom_iframe_autoload.js',
        "vicidial/static/src/js/services_icon_widget_copy.js",
        "vicidial/static/src/js/lead_form_close.js",
        # 'https://maps.googleapis.com/maps/api/js?key=AIzaSyB8_jft7R5en3Q4rrnLqsnuGEyg5_W7CHU&libraries=places',
        'vicidial/static/src/js/google_address_autocomplete.js',
        'vicidial/static/src/js/stage_scroll.js',

        # "vicidial/static/src/js/custom_footer.js",


    ],
},
}
