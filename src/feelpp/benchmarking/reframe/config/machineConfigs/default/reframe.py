import socket

hostname = socket.gethostname()

site_configuration = {
    'systems': [
        {
            'name': 'default',
            'descr': 'Default system',
            'hostnames': [f'{hostname}'],
            'partitions': [
                {
                    'name': 'default',
                    'scheduler': 'local',
                    'launcher': 'mpiexec',
                    'environs': ['default'],
                    'processor': { 'num_cpus': 4 }
                },
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
