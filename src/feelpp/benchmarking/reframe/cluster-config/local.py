site_configuration = {
    'systems': [
        {
            'name': 'local',
            'descr': 'Local desktop with 8 cpus',
            'hostnames': ['local'],
            'modules_system': 'nomod',
            'partitions': [
                {
                    'name': 'default',
                    'scheduler': 'local',
                    'launcher': 'mpiexec',
                    'environs': ['env_local'],
                    'processor': {
                        'num_cpus': 4
                    },
                    'devices': [
                        {
                            'name': 'cpu-node',
                            'num_devices': 1
                        }
                    ]
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
