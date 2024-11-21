site_configuration = {
    'systems': [
        {
            'name': 'gaya',
            'descr': 'Gaya',
            'hostnames': ['gaya'],
            'modules_system': 'tmod4',
            'partitions': [
                {
                    'name': 'production',
                    'scheduler': 'squeue',
                    'launcher': 'mpiexec',
                    'max_jobs': 8,
                    'access': ['--partition=production'],
                    'environs': ['builtin','apptainer','builtin_hpcx','apptainer_hpcx'],
                    'prepare_cmds': [
                        'source /etc/profile.d/modules.sh',
                        "export PATH=/opt/apptainer/v1.3.3/apptainer/bin/:$PATH"
                    ],
                    'processor': {
                        'num_cpus': 128
                    },
                    'devices': [
                        {
                            'type': 'cpu',
                            'num_devices': 4
                        }
                    ],
                    'container_platforms':[
                        {
                            'type': 'Apptainer'
                        }
                    ],
                },
            ],
            'env_vars':[
                ["OMP_NUM_THREADS",1]
            ]
        }
    ],
    'environments': [
        {
            'name': 'builtin',
            'modules': [],
            'cc': 'clang',
            'cxx': 'clang++',
            'target_systems': ['gaya:production']
        },
        {
            'name': 'builtin_hpcx',
            'modules': ['hpcx'],
            'cc': 'clang',
            'cxx': 'clang++',
            'target_systems': ['gaya:production']
        },
        {
            'name': 'apptainer',
            'modules': [],
            'cc': 'clang',
            'cxx': 'clang++',
            'target_systems': ['gaya:production']
        },
        {
            'name': 'apptainer_hpcx',
            'modules': ['hpcx'],
            'cc': 'clang',
            'cxx': 'clang++',
            'target_systems': ['gaya:production']
        }
    ]
}
