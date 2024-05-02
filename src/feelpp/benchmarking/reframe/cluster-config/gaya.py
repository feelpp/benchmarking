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
                    'max_jobs': 8,          # = default value
                    'access': ['--partition=public'],
                    'environs': ['env_gaya'],
                },
            ],
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
