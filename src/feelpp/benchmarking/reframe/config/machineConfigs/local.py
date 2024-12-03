site_configuration = {
    'systems': [
        {
            'name': 'local',
            'descr': 'Local desktop with 8 logical CPUs',
            'hostnames': ['local'],
            'modules_system': 'nomod',
            'partitions': [
                {
                    'name': 'default',
                    'scheduler': 'local',
                    'launcher': 'mpiexec',
                    'environs': ['default'],
                    'processor': {
                        'num_cpus': 8
                    },
                    'devices': [
                        {
                            'type': 'cpu',
                            'num_devices': 1
                        }
                    ]
                }
            ]
        }
    ],
    'environments': [
        {
            'name': 'default',
            'cc': 'clang',
            'cxx': 'clang++',
            'target_systems': ['local:default']
        }
    ]
}
