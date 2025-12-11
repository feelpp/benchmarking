from argparse import ArgumentParser
import os
from feelpp.benchmarking.json_report.renderer import JsonReportController



def main_cli():
    parser = ArgumentParser( description="Generates structured documents (like AsciiDoc) from a declarative JSON configuration file.", prog='json-report-render' )
    parser.add_argument( 'REPORT_FILE', type=str, help='The path to the declarative JSON report configuration file.' )
    parser.add_argument( '-o', '--output-dir', type=str, default='.', help='The directory where the final generated report will be saved.')
    parser.add_argument( '-f', '--output-format', type=str, default='adoc', choices=['adoc'], help='The format of the final document to be generated. Currently supports: adoc.' )
    parser.add_argument( '-n', '--output-name', type=str,default=None, help='A specific name for the output file (e.g., final_report.adoc). If not provided, the name is inferred from the REPORT_FILE.' )
    args = parser.parse_args()

    controller = JsonReportController( report_filepath=args.REPORT_FILE, output_format=args.output_format )
    output_path = controller.render( output_dirpath=args.output_dir, output_filename=args.output_name )
    print(f"✅ Report successfully generated at: {os.path.abspath(output_path)}")


if __name__ == "__main__":
    main_cli()