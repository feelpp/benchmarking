# system configuration for running test on .cpp files

site_configuration = {
    'systems': [
        {
            'name': 'localCFG',
            'descr': 'Config for local desktop',
            'hostnames': ['localCFG'],
            'modules_system': 'nomod',
            'partitions': [
                {
                    'name': 'default',
                    'scheduler': 'local',
                    'launcher': 'local',
                    'environs': ['gnu'],
                }
            ]
        }
    ],
    'environments': [
        {
            'name': 'gnu',
            'cc': 'gcc',
            'cxx': 'g++',
            'ftn': 'gfortran',
            'features': ['openmp'],
            'target_systems': ['localCFG']
        }
    ]
}