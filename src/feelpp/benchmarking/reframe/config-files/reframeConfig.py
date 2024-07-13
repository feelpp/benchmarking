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
            'target_systems': ['*'],
            'options': [
                '--exec-policy=serial'
            ]
        },
        {
            'name': 'async',
            'target_systems': ['*'],
            'options': [
                '--exec-policy=async'
            ]
        }
    ]
}
