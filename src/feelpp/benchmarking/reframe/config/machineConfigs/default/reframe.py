import socket

hostname = socket.gethostname()

site_configuration = {
    'systems': [
        {
            'name': 'default',
            'descr': 'Default System',
            'hostnames': [f'{hostname}'],
            'partitions': [
                {
                    'name': 'default',
                    'scheduler': 'squeue',
                    'launcher': 'mpiexec',
                    'max_jobs': 4,
                    'access': ['--partition=public'],
                    'environs': ['default'],
                    'prepare_cmds': [],
                    'processor': {
                        'num_cpus': 128
                    },
                    'resources': [
                        {
                            'name':'launcher_options',
                            'options':['-bind-to','core']
                        }
                    ],
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
            'modules': [],
            'cc': 'clang',
            'cxx': 'clang++',
            'target_systems': ['default:default']
        }
    ]
}
