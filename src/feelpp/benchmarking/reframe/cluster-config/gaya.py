site_configuration = {
    'systems': [
        {
            'name': 'gaya',
            'descr': 'Gaya',
            'hostnames': ['gaya'],
            'modules_system': 'nomod',
            'partitions': [
                {
                    'name': 'public',
                    'scheduler': 'squeue',
                    'launcher': 'mpiexec',
                    'max_jobs': 8,
                    'access': ['--partition=public'],
                    'environs': ['env_gaya'],
                    'processor': {
                        'num_cpus_per_socket': 64,
                        'num_sockets': 2
                    },
                    'devices': [
                        {
                            'name': 'cpu_node',
                            'num_devices': 6
                        }
                    ]
                },
            ]
        }
    ],
    'environments': [
        {
            'name': 'env_gaya',
            'cc': 'clang',
            'cxx': 'clang++',
            'target_systems': ['gaya:public']
        }
    ]
}
