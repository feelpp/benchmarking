import os,subprocess,shutil,glob
from argparse import ArgumentParser
from datetime import datetime
from feelpp.benchmarking.report.renderer import Renderer
from pathlib import Path

def initGit():
    print("initializing git repository...")
    subprocess.call(["git","init"])
    subprocess.call(["git","commit","--allow-empty","-m","init"])

def init(args):
    #Check destination exists
    if not os.path.isdir(args.destination):
        print(f"Destination {args.destination} is not a directory, creating it...")
        os.makedirs(args.destination)

    script_data_path = f"{Path(__file__).resolve().parent}/data/"

    #Copy package.json to destination
    shutil.copy(os.path.join(script_data_path,"package.json"),args.destination)

    #Init git repo at destination
    cwd = os.getcwd()
    os.chdir(args.destination)
    if not os.path.exists(".git"):
        initGit()

    #Install packages (npm install)
    subprocess.call(["npm","install"])

    #make pages and images dir
    if not os.path.isdir("docs/modules/ROOT/pages"):
        os.makedirs("docs/modules/ROOT/pages")

    if not os.path.isdir("docs/modules/ROOT/images"):
        os.mkdir("docs/modules/ROOT/images")

    #Add builtin images
    for img in glob.glob(os.path.join(script_data_path,"website_images","*")):
        shutil.copy(img,"docs/modules/ROOT/images")

    #Create index
    with open("docs/modules/ROOT/pages/index.adoc","w") as f:
        f.write(f"= {args.project_title}\n:page-layout: toolboxes\n:page-tags: catalog, catalog-index\n:docdatetime: {datetime.strftime(datetime.now(),'%Y-%m-%dT%H:%M:%S')}\n")

    #Create nav
    with open("docs/modules/ROOT/nav.adoc","w") as f:
        f.write(f"* xref:ROOT:index.adoc[{args.project_title}]")

    #Create antora component version descriptor
    Renderer(script_data_path,"antora.yml.j2").render( "./docs/antora.yml", dict( project_name = args.project_name, project_title = args.project_title ) )

    #Create antora playbook
    Renderer(script_data_path,"site.yml.j2").render( "./site.yml", dict( project_name = args.project_name, project_title = args.project_title ) )

def main_cli():
    parser = ArgumentParser(prog="feelpp-antora")
    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser('init')

    init_parser.add_argument("--destination",'-d', required=False, default=".",type=str,help="Base directory where to initialize antora files.")
    init_parser.add_argument("--project-title",'-t', required=True, type=str, help="The title of your project.")
    init_parser.add_argument("--project-name",'-n', required=True, type=str, help="The name of your project. Must not contain spaces or any special characters other than underscore (_)")
    init_parser.set_defaults(func=init)

    args = parser.parse_args()
    args.func(args)

    return 0