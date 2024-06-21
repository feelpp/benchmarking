#!/bin/bash

usage() {
    echo "Usage: $0 <machine> [-a|--all] [-tb name|--toolbox=name] [-c path|--case=path] [-h|--help]"
    echo "  <machine>                   Name of the machine "
    echo "  -a, --all                   Launch every testcase from every toolbox"
    echo "                              (default if no toolbox provided)"
    echo "  -tb name, --toolbox name    Name of the toolbox (multiple names separated by ':')"
    echo "  -c path, --case path        Path to the case .cfg file (multiple paths separated by ':', requires -tb)"
    echo "  -h, --help                  Display help"
}

# Check for --help option
if [ "$*" == "-h" ] || [ "$*" == "--help" ]; then
    usage
    exit 0
fi

valid_machines=("discoverer" "gaya" "karolina" "local" "meluxina")

# Check for obligatory arguments (=machine)
if [ $# -lt 1 ] || ! [[ " ${valid_machines[*]} " == *" $1 "* ]]; then
    usage
    exit 1
fi


# Assign the first argument as <machine>
machine=$1
shift

# Initialiser les variables pour les options
option_a=0
toolboxes=()
cases=()

# Traiter les options
while [ $# -gt 0 ]; do
    case "$1" in
        -a|--all)
            option_a=1
            shift
            ;;
        -tb|--toolbox)
            if [[ "$2" != "" && "$2" != -* ]]; then
                if [[ "$2" == *=* ]]; then
                    toolboxes+=("${2#*=}")
                    shift 2
                else
                    shift
                    toolboxes+=("$1")
                    shift
                fi
            else
                echo "Error: Option -tb|--toolbox requires a non-empty argument."
                usage
                exit 1
            fi
            ;;
        -c|--case)
            if [[ "$2" != "" && "$2" != -* ]]; then
                if [[ "$2" == *=* ]]; then
                    IFS=':' read -r -a cases <<< "${2#*=}"
                    shift 2
                else
                    shift
                    IFS=':' read -r -a cases <<< "$1"
                    shift
                fi
            else
                echo "Error: Option -c|--case requires a non-empty argument."
                usage
                exit 1
            fi
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        --)
            shift
            break
            ;;
        *)
            echo "Error: Invalid option: $1"
            usage
            exit 1
            ;;
    esac
done

# Vérifier si --case est fourni sans --toolbox
if [ ${#cases[@]} -gt 0 ] && [ ${#toolboxes[@]} -eq 0 ]; then
    echo "Error: -c|--case requires -tb|--toolbox to be specified."
    usage
    exit 1
fi

# Logique du script en fonction des options
echo "Machine name: $machine"

if [ $option_a -eq 1 ]; then
    echo "Option A activée : Lancer tous les cas de test de toutes les boîtes à outils"
fi

if [ ${#toolboxes[@]} -ne 0 ]; then
    echo "Selected toolboxes: ${toolboxes[*]}"
fi

if [ ${#cases[@]} -ne 0 ]; then
    echo "Selected cases: ${cases[*]}"
fi

# Afficher les arguments restants
if [ $# -gt 0 ]; then
    echo "Remaining arguments: $@"
fi

# Logique pour lancer les tests pour chaque boîte à outils sélectionnée
for toolbox in "${toolboxes[@]}"; do
    echo "Launching tests for toolbox: $toolbox"
    for case_path in "${cases[@]}"; do
        echo "Using case file: $case_path"
        # Ajouter la logique pour utiliser le fichier de cas spécifique pour cette toolbox
    done
    # Ici, ajouter la logique pour lancer les tests pour chaque toolbox
done
