site_configuration = {
    'systems':[
        {
            'name': 'discoverer',
            'descr': 'Discoverer',
            'hostnames': ['login\d+.discoverer.sofiatech.bg','cn*'],
            'modules_system': 'tmod4',
            'partitions': [
                {
                    'name': 'cn',
                    'scheduler': 'slurm',
                    'launcher': 'srun',
                    'max_jobs': 8,
                    'access': ['--partition=cn --account=ehpc-dev-2024d05-047 --qos=ehpc-dev-2024d05-047'],
                    'environs': ['default'],
                    'prepare_cmds': [
                        'source /etc/profile.d/modules.sh',
                        'export MODULEPATH=/opt/software/modulefiles',
                        'export OMP_NUM_THREADS=1' # Just in case
                    ],
                    'processor': {
                        'num_cpus': 128
                    },
                    'devices': [
                        {
                            'type': 'cpu',
                            'num_devices': 1320 #VALIDATE
                        }
                    ],
                    'container_platforms':[
                        {
                            'type': 'Singularity'
                        }
                    ],
                    'sched_options': { 'use_nodes_option': True },
                }
            ],
            'env_vars':[
                ["OMP_NUM_THREADS",1]
            ]
        }
    ],
    'environments': [
        {
            'name':'default',
            'modules': [],
            'target_systems':['discoverer:cn']
        }
    ]
}