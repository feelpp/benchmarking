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
                    'access': ['--partition=public'],
                    'environs': ['env_gaya'],
                },
            ],
            #'max_jobs': 8,      # 'max_jobs': Max number of concurrent launched jobs. Default: 8
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
