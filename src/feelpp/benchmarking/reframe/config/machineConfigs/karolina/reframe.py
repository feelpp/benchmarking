site_configuration = {
    'systems': [
        {
            'name': 'karolina',
            'descr': 'karolina',
            'hostnames': ['login\d+.karolina.it4i.cz','cn\d+.karolina.it4i.cz'],
            'modules_system': 'lmod',
            'partitions': [
                {
                    'name': 'qcpu',
                    'scheduler': 'slurm',
                    'launcher': 'srun',
                    'max_jobs': 8,
                    'access': ['--partition=qcpu'],
                    'environs': ['default'],
                    'processor': {
                        'num_cpus': 128
                    },
                    'devices': [
                        {
                            'type': 'cpu',
                            'num_devices':829
                        }
                    ],
                    'container_platforms':[
                        {
                            'type': 'Singularity'
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
            'modules': ['OpenMPI/4.1.4-GCC-12.2.0','apptainer'],
            'target_systems': ['karolina:qcpu']
        }
    ]
}