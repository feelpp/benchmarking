site_configuration = {
    'systems': [
        {
            'name': 'localCFG',
            'descr': 'Local desktop with mpiexec',
            'hostnames': ['localCFG'],
            'modules_system': 'nomod',
            'partitions': [
                {
                    'name': 'default',
                    'scheduler': 'local',
                    'launcher': 'mpiexec',
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
            'target_systems': ['localCFG']
        }
    ]
}
