site_configuration = {
    'general': [
        {
            'report_file': '${HOME}/COUCOU.json',
            #'remote_detect': True
        }
    ],
    'modes': [
        {
            'name': 'serial',
            'options': [
                '--exec-policy=serial'
            ]
        },
        {
            'name': 'async',
            'options': [
                '--exec-policy=aysnc'
            ]
        }
    ]
}
