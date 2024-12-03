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
                        'export PATH=/opt/apptainer/v1.3.3/apptainer/bin/:$PATH' #NEEDED ?
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
            'name':'default',
            'modules': ['python/3/3.9/latest','openmpi/4/gcc/latest'],
            'target_systems':['discoverer:cn']
        }
    ]
}