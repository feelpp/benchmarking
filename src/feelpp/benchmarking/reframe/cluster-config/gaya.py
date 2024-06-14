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
                        'num_cpus': 128
                    },
                    'devices': [
                        {
                            'name': 'cpu_node',
                            'num_devices': 1        # --> to be set to 6 when MPI_ERR_TRUNCATE resolved
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
