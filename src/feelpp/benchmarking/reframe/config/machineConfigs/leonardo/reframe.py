import socket

hostname = socket.gethostname()
site_configuration = {
    'systems': [
        {
            'name': 'leonardo',
            'descr': 'Leonardo',
            'hostnames': [f'{hostname}'],
            'modules_system': 'lmod',
            'partitions': [
                {
                    'name': 'dcgp_usr_prod',
                    'scheduler': 'slurm',
                    'launcher': 'srun',
                    'max_jobs': 8,
                    'access': ['--partition=dcgp_usr_prod'],
                    'environs': ['default'],
                    'processor': {
                        'num_cpus':112
                    },
                    'devices':[
                        {
                            'type': 'cpu',
                            'num_devices': 1536
                        }
                    ],
                    'container_platforms':[
                        {
                            'type': 'Singularity',
                        }
                    ],
                    'extras':{
                        'memory_per_node': 500 #512 in reality
                    }
                }
            ]
        }

    ],
    'environments': [
        {
            'name': 'default',
            'modules': ['openmpi/4.1.6--gcc--12.2.0'],
            'target_systems': ['leonardo:dcgp_usr_prod']
        }
    ]
}