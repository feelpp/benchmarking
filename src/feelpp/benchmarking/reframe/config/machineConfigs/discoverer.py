from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv(os.path.join(Path(__file__).resolve().parent,"hpc.env"))

project_id = os.getenv("discoverer_project_id")

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
                    'access': [f"--partition=cn --account={project_id} --qos={project_id}"],
                    'environs': ['default'],
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
            'modules': ["openmpi/4/gcc/latest"],
            'target_systems':['discoverer:cn'],
            'prepare_cmds': [
                'source /etc/profile.d/modules.sh',
                'export MODULEPATH=/opt/software/modulefiles:$MODULEPATH'
            ]
        }
    ]
}