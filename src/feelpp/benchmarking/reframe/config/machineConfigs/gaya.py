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
                    'environs': ['env_gaya'],
                    'prepare_cmds': ['source /etc/profile.d/modules.sh'],
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
                            'type': 'Apptainer',
                        }
                    ],
                },
            ]
        }
    ],
    'environments': [
        {
            'name': 'env_gaya',
            'modules': ['hpcx'],
            'cc': 'clang',
            'cxx': 'clang++',
            'target_systems': ['gaya:public']
        }
    ]
}
