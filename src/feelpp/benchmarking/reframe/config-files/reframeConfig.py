
""" --- ??? Are modes really needed for our purpose ??? --- """

site_configuration = {

    'general': [
        {
            #'report_file': '${MY_WORKDIR}/COUCOU.json',
            #'remote_detect': True
        }
    ],

    'modes': [
        {
            'name': 'CpuVariation',
            'target_systems': ['*'],
            'options':
            [
                '-c $RFM_TEST_DIR/cpuVariation.py',
                '-r',
                #f'-S case=$FEELPP_CFG_PATHS',
                '--exec-policy=serial'
            ]
        }
    ]
}
