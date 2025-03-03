# The feelpp.benchmarking Project

![CI](https://github.com/feelpp/benchmarking/workflows/CI/badge.svg)

The `feelpp.benchmarking` framework is designed to automate and facilitate the benchmarking process for any application. It enables hightly customized and flexible benchmarking, providing a pipeline that guides users from test execution to comprehensive report generation.
The framework is built on top of [ReFrame-HPC](https://reframe-hpc.readthedocs.io/en/stable/index.html) and leverages a modular configuration system based on three JSON files that define machine-specific options, benchmark parameters, and dashboard report figures.

Key features include:

* Tailored Configuration:
Separate JSON files allow for detailed setup of machine environments, benchmark execution (including executable paths and test parameters), and report formatting. The use of placeholder syntax facilitates easy refactoring and reuse.
* Automated and Reproducible Workflows:
The pipeline validates input configurations, sets up execution environments via ReFrame, and runs benchmarks in a controlled manner. Results are gathered and transformed into comprehensive, reproducible reports.
* Container Integration:
With support for Apptainer (or Singularity), the framework ensures that benchmarks can be executed consistently across various HPC systems.
* Continuous Benchmarking:
The integration with CI/CD pipelines enables ongoing performance tracking. This is especially useful in projects where monitoring application scaling and performance over time is critical.

The feelpp.benchmarking tool serves as a centralized platform for aggregating benchmarking results into a clear dashboard, making it an essential resource for those looking to monitor and enhance HPC application performance.

## Installation

### Using PyPi

* Use a python virtual environment (Optional)

```bash
python3 -m venv .venv
source .venv/bin/activate
```

* Install the package

```bash
pip install feelpp-benchmarking
```

### Using Git

* Clone the repository

```bash
git clone https://github.com/feelpp/benchmarking.git
```

* Use a python virtual environment (Optional)

```bash
python3 -m venv .venv
source .venv/bin/activate
```

* Install the project and dependencies

```bash
python3 -m pip install .
```

## Prerequisites

In order to generate the benchmark reports website, Antora must be configured beforehand, along with the necessary extensions. More information can be found in [Antora Documentation](https://docs.antora.org/antora/latest/install-and-run-quickstart/)

* Make sure you have [Node.js](http://nodejs.org/en/download) installed.

<dl><dt><strong>❗ IMPORTANT</strong></dt><dd>

The following part of prerequisites is only necessary if the `feelpp.benchmarking` repository is not being cloned.
</dd></dl>

* A local git repository is needed, so if you are not adding `feelpp.benchmarking` to an existing repository:

```bash
git init
git commit --allow-empty -m init
```

* Download the [package.json](https://github.com/feelpp/benchmarking/blob/master/package.json) dependency file and place it at the root of your project.
* Install dependencies

```bash
npm install
```

* Create the Antora’s [standard directory hierarchy](https://docs.antora.org/antora/latest/standard-directories/).

```bash
mkdir -p docs/modules/ROOT/pages
```

* Create the start and navigation pages

```bash
echo "= <YOUR-PROJECT-TITLE>\n:page-layout: toolboxes\n:page-tags: catalog, catalog-index\n:docdatetime: 2025-01-22T11:42:45" > docs/modules/ROOT/pages/index.adoc
```

```bash
echo "* xref:ROOT:index.adoc[YOUR-PROJECT-TITLE]" > docs/modules/ROOT/nav.adoc
```

* Write the component version descriptor.

```bash
touch docs/antora.yml
```

Write the following in the file.

```yaml
name: <PROJECT-NAME>
title: <YOUR-PROJECT-TITLE>
version: ~
start_page: index.adoc
asciidoc:
  attributes:
    project_name: <YOUR-PROJECT-TITLE>
    numbered: true
    dynamic-blocks@: ''
    allow-uri-read: true
    hide-uri-scheme: true
nav:
  - modules/ROOT/nav.adoc
```

* Create the antora playbook at the root of your project

```bash
touch ./site.yml
```

Write the following to the file

```yaml
site:
  title: <YOUR-PROJECT-TITLE>
  start_page: <YOUR-PROJECT-NAME>::index.adoc
content:
  sources:
  - url: .
    branches: HEAD
    start_path: docs
ui:
  bundle:
    url: https://github.com/feelpp/antora-ui/releases/latest/download/ui-bundle.zip
    snapshot: true
output:
  clean: true
  dir: public
asciidoc:
  extensions:
  - '@feelpp/asciidoctor-extensions'
```

<dl><dt><strong>❗ IMPORTANT</strong></dt><dd>

Make sure to replace the values of `<YOUR-PROJECT-NAME>` and `<YOUR-PROJECT-TITLE>` with the actual values.
</dd></dl>

## Quickstart

For detailed documentation, refer to our [docs](https://bench.feelpp.org/benchmarking/tutorial/index.html).

### The benchmarked application

The framwork includes a sample C++/MPI application that can be used to get familiar with the framework’s core concepts. It can be found under _tests/data/parallelSum.cpp_, or you can download it here : [parallelSum.cpp](https://github.com/feelpp/benchmarking/blob/master/tests/data/parallelSum.cpp)

This Feel++ Benchmarking "Hello World" application will compute the sum of an array distributed across multiple MPI processes. Each process will compute a partial sum, and then it will be summed to get the total sum.

Additionally, the app will measure the time taken to perform the partial sum, and will save it under a _scalability.json_ file.

You can update the sample application and recompile it for a specific config as needed.
```bash
mpic++ -std=c++17 -o test/data/parallelSum test/data/parallelSum.cpp
```

### Machine configuration files

The framework also contains a default system configuration, located under _config/machines/default.json_ corresponding to the file _src/feelpp/benchmarking/reframe/config/machineConfigs/default/reframe.py, that looks like this :

```json
{
   //will use the `default` ReFrame configuration file
   "machine": "default",

   //will run on the default partition, using the built-in (or local) platform and the default env
   "targets":["default:builtin:default"],

   //Tests will run asynchronously (up to 4 jobs at a time)
   "execution_policy": "async",

   // ReFrame's stage and output directories will be located under _./build/reframe/_
   "reframe_base_dir":"./build/reframe",

   // The generated JSON report will be created under _./reports/_
   "reports_base_dir":"./reports/",

   // The base directory where the executable is located
   "input_dataset_base_dir":"$PWD",

   //The C++ app outputs will be stored under the current working directory (./)
   "output_app_dir":"$PWD"
}
```
You can download this configuration file here [default.json](https://github.com/feelpp/benchmarking/blob/master/config/machines/default.json).

The framework also contains a very basic sample ReFrame configuration file, under _config/machines/default.py_. [default.py](https://github.com/feelpp/benchmarking/blob/master/config/machines/default.py)

This file will cause the tool to use a local scheduler and the `mpiexec` launcher with no options. For more advanced configurations, refer to [ReFrame’s configuration reference](https://reframe-hpc.readthedocs.io/en/stable/config_reference.html#)

More information on _feelpp.benchmarking_ machine configuration files can be found on the documentation [Machine configuration](https://bench.feelpp.org/benchmarking/tutorial/configuration.html#_machine_configuration)

### Benchmark configuration files

Along with machine configuration files, users must provide the specifications of the benchmark. A sample file is provided under _config/tests_parallelSum/parallelSum.json_. [parallelSum.json](https://github.com/feelpp/benchmarking/blob/master/config/tests_parallelSum/parallelSum.json)

```json
{
   //Executable path (Change the location to the actual executable)
   "executable": "{{machine.input_dataset_base_dir}}/tests/data/parallelSum",
   "use_case_name": "parallel_sum",
   "timeout":"0-0:5:0",
   "output_directory": "{{machine.output_app_dir}}/tests/data/outputs/parallelSum",

   //Application options
   "options": [ "{{parameters.elements.value}}", "{{output_directory}}/{{instance}}" ],

   //Files containing execution times
   "scalability": {
      "directory": "{{output_directory}}/{{instance}}/",
      "stages": [
         {
            "name":"",
            "filepath": "scalability.json",
            "format": "json",
            "variables_path":"*"
         }
      ]
   },

   // Resources for the test
   "resources":{
      "tasks":"{{parameters.tasks.value}}"
   },

   // Files containing app outputs
   "outputs": [
      {
         "filepath":"{{output_directory}}/{{instance}}/outputs.csv",
         "format":"csv"
      }
   ],

   // Test validation (Only stdout supported at the moment)
   "sanity": { "success": ["[SUCCESS]"], "error": ["[OOPSIE]","Error"] },

   // Test parameters
   "parameters": [
      {
         "name": "tasks",
         "sequence": [1,2,4]
      },
      {
         "name":"elements",
         "linspace":{ "min":100000000, "max":1000000000, "n_steps":4 }
      }
   ]
}
```

<dl><dt><strong>🔥 CAUTION</strong></dt><dd>

Remember to modify the `executable` path as well as `output_directory` if installing via pip.
</dd></dl>

More information about _feelpp.benchmarking_ benchmark specifications can be found [here](https://bench.feelpp.org/benchmarking/tutorial/configuration.html#_benchmark_configuration)

### Plots configuration

Along with the benchmark configuration, a figure configuration file is provided _config/test\_parallelSum/plots.json_ Download it here [plots.json](https://github.com/feelpp/benchmarking/blob/master/config/tests_parallelSum/plots.json).

An example of one figure specification is shown below. Users can add as many figures as they wish, corresponding the figure axis with the parameters used on the benchmark.
```json
{
   "title": "Absolute performance",
   "plot_types": [ "stacked_bar", "grouped_bar" ],
   "transformation": "performance",
   "variables": [ "computation_time" ],
   "names": ["Time"],
   "xaxis":{ "parameter":"resources.tasks", "label":"Number of tasks" },
   "yaxis":{"label":"Execution time (s)"},
   "secondary_axis":{ "parameter":"elements", "label":"N" }
}
```

More information about _feelpp.benchmarking_ figure configuration can be found [here](https://bench.feelpp.org/benchmarking/tutorial/configuration.html#_figures)

### Running a benchmark
Finally, to benchmark the test application, generate the reports and plot the figures, run (changing the file paths as needed)
```bash
execute-benchmark --machine-config config/machines/default.json \
                  --custom-rfm-config config/machines/default.py \
                  --benchmark-config config/test_parallelSum/parallelSum.json \
                  --plots-config config/test_parallelSum/plots.json \
                  --website
```

The `--website` option will start an http-server on localhost, so the website can be visualized. Check the console for more information.

<dl><dt><strong>🔥 CAUTION</strong></dt><dd>

If you installed the framework via PyPi:

* You need to directly download all 5 quickstart files.
* The `--website` option will only work if you have the exact antora setup as this repository.
</dd></dl>

## Usage

### Executing a benchmark

In order to execute a benchmark, you can make use of the `execute-benchmark` command after all configuration files have been set ( [Configuration Reference](tutorial:configuration.adoc)).

The script accepts the following options :

    `--machine-config`, (`-mc`)
                          Path to JSON reframe machine configuration file, specific to a system.
    `--plots-config`, (`-pc`)   Path to JSON plots configuration file, used to generate figures. 
                          If not provided, no plots will be generated. The plots configuration can also be included in the benchmark configuration file, under the "plots" field.
    `--benchmark-config`, (`-bc`)
                          Paths to JSON benchmark configuration files 
                          In combination with `--dir`, specify only provide basenames for selecting JSON files.
    `--custom-rfm-config`, (`-rc`)
                          Additional reframe configuration file to use instead of built-in ones. It should correspond the with the `--machine-config` specifications.
    `--dir`, (`-d`)             Name of the directory containing JSON configuration files
    `--exclude`, (`-e`)         To use in combination with `--dir`, mentioned files will not be launched. 
                          Only provide basenames to exclude.
    `--move-results`, (`-mv`)   Directory to move the resulting files to. 
                          If not provided, result files will be located under the directory specified by the machine configuration.
    `--list-files`, (`-lf`)     List all benchmarking configuration file found. 
                          If this option is provided, the application will not run. Use it for validation.
    `--verbose`, (`-v`)         Select Reframe's verbose level by specifying multiple v's. 
    `--help`, (`-h`)            Display help and quit program
    `--website`, (`-w`)         Render reports, compile them and create the website.
    `--dry-run`             Execute ReFrame in dry-run mode. No tests will run, but the script to execute it will be generated in the stage directory. Config validation will be skipped, although warnings will be raised if bad.

When a benchmark is done, a `website_config.json` file will be created (or updated) with the current filepaths of the reports and plots generated by the framework. If the `--website` flag is active, the `render-benchmarks` command will be launched with this file as argument.

### Rendering reports

To render reports, a webiste configuration file is needed. An example is provided under _src/benchmarking/reports/config/config.json_. This file indicates how the website views should be structured, and it indicates the hierarchy of the benchmarks.

A file of the same type is generated after a benchmark is launched, called _website_config.json_, and it is found at the root of the _reports_ directory specified under the `reports_base_dir` field of machine configuration file ( xref:tutorial:configfiles/machine.adoc).

Once this file is located, users can run the `render-benchmarks` command to render existing reports.

The script takes the following arguments:

    `--config-file` (`-c`): The path of the website configuration file.
    `--remote-download-dir` (`-do`): [Optional] Path of the directory to download the reports to. Only relevant if the configuration file contains remote locations (only Girder is supported at the moment).
    `--modules-path` (`-m`): [Optional] Path to the Antora module to render the reports to. It defaults to _docs/modules/ROOT/pages_. Multiple directories will be recursively created under the provided path.
    `--overview-config` (`-oc`): Path to the overview figure configuration file.
    `--plot-configs` (`-pc`): Path the a plot configuration to use for a given benchmark. To be used along with --patch-reports
    `--patch-reports` (`-pr`) : Ids of the reports to path, the syntax of the id is machine:application:usecase:date e.g. gaya:feelpp_app:my_use_case:2024_11_05T01_05_32. It is possible to affect all reports in a component by replacing the machine, application, use_case or date by 'all'. Also, one can indicate to patch the latest report by replacing the date by 'latest'. If this option is not provided but plot-configs is, then the latest report will be patched (most recent report date)
    `--save-patches` (`-sp`) : If this flag is active, existing plot configurations will be replaced with the ones provided in patch-reports.
    `--website` (`-w`) : [Optional] Automatically compite the website and start an http server.
