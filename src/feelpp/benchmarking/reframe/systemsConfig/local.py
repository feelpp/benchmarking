site_configuration = {
    'systems': [
        {
            'name': 'local',
            'descr': 'Local desktop with mpiexec',
            'hostnames': ['local'],
            'modules_system': 'nomod',
            'partitions': [
                {
                    'name': 'default',
                    'scheduler': 'local',
                    'launcher': 'mpiexec',
                    'environs': ['env_local'],
                }
            ]
        }
    ],
    'environments': [
        {
            'name': 'env_local',
            'cc': 'gcc',
            'cxx': 'g++',
            'ftn': 'gfortran',
            'target_systems': ['local:default']
        }
    ]
}
