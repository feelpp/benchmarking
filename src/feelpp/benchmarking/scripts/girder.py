from feelpp.benchmarking.report.config.handlers import GirderHandler
from argparse import ArgumentParser



def download_cli():
    parser = ArgumentParser()
    parser.add_argument("--girder_id", '-gid', required = True, type=str, help="Girder file id to download.")
    parser.add_argument("--directory","-d", action='store_true', help="Set this flag if the target is a directory")
    parser.add_argument("--output_dir", '-o', required = False, type=str, help="Path to the directory to download files to.", default="./tmp/")
    parser.add_argument("--filename", '-fn', required = False, type=str, default=None, help="Name to give to the file after downloading ")
    args = parser.parse_args()

    girder_hanlder = GirderHandler(args.output_dir)
    if args.directory:
        girder_hanlder.downloadFolder(args.girder_id,output_dir=".")
    else:
        girder_hanlder.downloadFile(args.girder_id,name=args.filename)

    return 0

def upload_cli():
    parser = ArgumentParser()
    parser.add_argument("--item", required=True, help="Path of the directory or file to upload as an item")
    parser.add_argument("--girder_id", required=True, help="The Girder folder ID to which to upload the item")
    args = parser.parse_args()

    girder_handler = GirderHandler(download_base_dir=None)
    girder_handler.upload( args.item, args.girder_id )

    return 0