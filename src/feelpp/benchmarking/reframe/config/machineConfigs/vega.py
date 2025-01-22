import socket

hostname = socket.gethostname()
print("Hostname:", hostname)

site_configuration = {
    'systems':[
        {
            'name': 'vega',
            'descr': 'Vega',
            'hostnames': [f'{hostname}'],
            'modules_system': 'lmod',
            'partitions': [
                {
                    'name': 'cpu',
                    'scheduler': 'slurm',
                    'launcher': 'srun',
                    # 'max_jobs': 8,
                    'access': [f"--partition=cpu"],
                    'environs': ['default'],
                    'processor': {
                        'num_cpus': 128
                    },
                    'devices': [
                        {
                            'type': 'cpu',
                            'num_devices': 960
                        }
                    ],
                    'container_platforms':[
                        {
                            'type': 'Singularity'
                        }
                    ],
                    'sched_options': { 'use_nodes_option': True },
                    'extras':{
                        'memory_per_node':256
                    }
                }
            ]
        }
    ],
    'environments': [
        {
            'name':'default',
            'modules': ["OpenMPI/4.1.5-GCC-12.3.0"],
            'target_systems':['vega:cpu']
        }
    ]
}