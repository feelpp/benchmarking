import socket

hostname = socket.gethostname()
print("Hostname:", hostname)

site_configuration = {
    'systems': [
        {
            'name': 'meluxina',
            'descr': 'meluxina',
            'hostnames': [f'{hostname}'],
            'modules_system': 'lmod',
            'partitions': [
                {
                    'name': 'cpu',
                    'scheduler': 'slurm',
                    'launcher': 'srun',
                    'max_jobs': 8,
                    'access': ['--partition=cpu'],
                    'environs': ['default'],
                    'processor': {
                        'num_cpus': 128
                    },
                    'devices':[
                        {
                            'type': 'cpu',
                            'num_devices': 573
                        }
                    ],
                    'container_platforms':[
                        {
                            'type': 'Apptainer',
                        }
                    ],
                    'extras':{
                        'memory_per_node':512
                    }
                }
            ]
        }

    ],
    'environments': [
        {
            'name': 'default',
            'modules': [' env/staging/2023.1', 'Apptainer/1.2.4-GCCcore-12.3.0', 'OpenMPI/4.1.5-GCC-12.3.0'],
            'target_systems': ['meluxina:cpu']
        }
    ]
}