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
                    'access': ['--partition=cn'], #ENV VAR? TODO: add --account and --qos
                    'environs': ['apptainer'],
                    'prepare_cmds': [
                        'source /etc/profile.d/modules.sh',
                        'export MODULEPATH=/opt/software/modulefiles',
                        'export PATH=/opt/apptainer/v1.3.3/apptainer/bin/:$PATH' #NEEDED ?
                    ],
                    'processor': {
                        'num_cpus': 128 #VALIDATE
                    },
                    'devices': [
                        {
                            'type': 'cpu',
                            'num_devices': 1320 #VALIDATE
                        }
                    ],
                    'container_platforms':[
                        {
                            'type': 'Apptainer' # DOES IT WORK ? OR NEED 'Singularity'?
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
            'name':'apptainer',
            'modules': ['python/3/3.9/latest','openmpi/4/gcc/latest'],
            'target_systems':['discoverer:cn']
        }
    ]
}