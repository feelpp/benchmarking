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
                    'environs': ['default','hpcx'],
                    'prepare_cmds': [
                        'source /etc/profile.d/modules.sh',
                        "export PATH=/opt/apptainer/v1.3.5/apptainer/bin/:$PATH"
                    ],
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
                            'num_devices': 4
                        }
                    ],
                    'container_platforms':[
                        {
                            'type': 'Apptainer'
                        }
                    ],
                    'extras':{
                        'memory_per_node':500
                    }
                },
                {
                    'name':'gpu',
                    'scheduler':'squeue',
                    'launcher':'local',
                    'max_jobs':4,
                    'access': ['--partition=gpu'],
                    'environs': ['default'],
                    'prepare_cmds': [
                        'source /etc/profile.d/modules.sh',
                        "export PATH=/opt/apptainer/v1.3.5/apptainer/bin/:$PATH"
                    ],
                    'processor': {
                        'num_cpus': 32
                    },
                    'devices': [
                        {
                            'type': 'gpu',
                            'num_devices': 3
                        }
                    ],
                    'container_platforms':[
                        {
                            'type': 'Apptainer'
                        }
                    ],
                    'extras':{
                        'memory_per_node':256
                    }
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
            'target_systems': ['gaya:production','gaya:gpu']
        },
        {
            'name': 'hpcx',
            'modules': ['hpcx'],
            'cc': 'clang',
            'cxx': 'clang++',
            'target_systems': ['gaya:production']
        }
    ]
}
