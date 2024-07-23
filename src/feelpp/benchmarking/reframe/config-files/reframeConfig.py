site_configuration = {

    'general': [
        {
            # Where to put report_file ?
            # General configuration OR mode OR command line ?
            #'report_file': '${HOME}/COUCOU.json',
            #'remote_detect': True
        }
    ],

    'modes': [
        {
            'name': 'CpuVariation',
            'target_systems': ['*'],
            'options':
            [
                '-c $RFM_TEST_DIR/cpuVariation.py',      # check if guillemets needed
                #'-S sequence=$sequence',
                '-r',                                   # -r=run, -l=list
                #f'-S case=$FEELPP_CFG_PATHS',         
                '--exec-policy=serial'
            ]
        },

        {
            'name': 'ModelVariation',
            'target_systems': ['*'],
            'options': [
                '-c $RFM_TEST_DIR/modelVariation.py',      # check if guillemets needed
                '-S case=$cfgPath',
                '-S sequence=$sequence',
                '-r',                                   # -r=run, -l=list
                '--system=$hostname',
                '--report-file=$report_path',
                '--exec-policy=serial'
            ]
        },

        {
            'name': 'TEST',
            'target_systems': ['*'],
            'options': [
                '--show-config',
                '--exec-policy=serial',
                '--system=$HOSTNAME'
            ]
        }
    ]
}
