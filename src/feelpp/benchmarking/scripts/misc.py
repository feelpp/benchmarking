from argparse import ArgumentParser
import glob, json, copy

def mergeDicts(dict1, dict2):
    """Recursively merges two dictionaries."""
    merged = copy.deepcopy(dict1)  # Make a deep copy of the first dictionary
    for key, value in dict2.items():
        if key in merged:
            if isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = mergeDicts(merged[key], value)
            elif isinstance(merged[key], list) and isinstance(value, list):
                merged[key] = list(set(merged[key] + value))
            else:
                merged[key] = value
        else:
            merged[key] = value
    return merged




def jsonConfigMerge_cli():
    """ Merge multiple json files into a single one"""
    parser = ArgumentParser()
    parser.add_argument("--file_pattern", '-fp', required = True, type=str, help="File glob pattern of the json files to merge")
    parser.add_argument("--output_file_path","-o",required=True,type=str,help="Path of the resulting file to be saved to")
    args = parser.parse_args()

    master_config = {}
    for filename in glob.glob(args.file_pattern,recursive=True):
        with open(filename,"r") as f:
            current_config = json.load(f)
            master_config = mergeDicts(master_config,current_config)

    with open(args.output_file_path,"w") as f:
        f.write(json.dumps(master_config))

    return 0