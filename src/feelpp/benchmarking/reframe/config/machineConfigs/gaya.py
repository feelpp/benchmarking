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
                    'sched_options': { 'use_nodes_option': True },
                    'environs': ['builtin','apptainer'],
                    'prepare_cmds': [
                        'source /etc/profile.d/modules.sh',
                        "export PATH=/opt/apptainer/v1.3.5/apptainer/bin/:$PATH"
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
        }
    ]
}
