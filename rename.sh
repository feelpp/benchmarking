#! /bin/bash

# This script is used to rename the project from myproject to something else.

create_name(){
    string=$1
    # Use parameter expansion to get the second part of the string
    second_part="${string#*/}"
    echo "$second_part"
}
create_short_name() {
    name=$1
    # Convert the name to lowercase and remove spaces
    short_name=$(echo "$name" | tr '[:upper:]' '[:lower:]' | sed 's/ //g')

    # Get the first word
    first_word=$(echo "${short_name%%-*}")
    #echo "First word: $first_word"
    # Get the other words and their first letters
    other_words=$(echo "${short_name}" | tr '-' '\n' | cut -c1 | tr -d '\n')
    #echo "Other words: $other_words"
    # Combine the first word and other letters to create a shorter name
    #shorter_name="${first_word}-${other_words}"
    shorter_name="${other_words}"

    # Print the shorter name
    echo "$shorter_name"
}
create_title() {
    name=$1
# Convert the name to lowercase and remove spaces
short_name=$(echo "$name" | tr '[:upper:]' '[:lower:]' | sed 's/ //g')

# Replace hyphens with spaces
short_name=${short_name//-/ }

# Use parameter expansion to uppercase the first letter of each word
uppercase_name=$(echo "$short_name" | awk '{for(i=1;i<=NF;i++)sub(/./,toupper(substr($i,1,1)),$i)}1')


    # Print the shorter name
    echo "$uppercase_name"
}

# This script is used to rename the project from myproject to something else.
if [ -z "$1" ]; then
    echo "Usage: $0 <projectname> <projecttitle> <shortprojectname> <appname>"
    exit 1
elif [ "$1" == "-h" -o "$1" == "--help" ]; then
    echo "Usage: $0 <projectname> <projecttitle> <shortprojectname> <appname>"
    exit 1
elif [ "$1" == "-r" ]; then
    in_default_projectname="project"
    read -p "What is the name of the project ? [$in_default_projectname]: " projectname
    projectname=${projectname:-$in_default_projectname}

    in_default_titlename="$projectname"
    read -p "What is the title of the project? [$in_default_titlename]" projecttitle
    projecttitle=${projecttitle:-$in_default_titlename}

    in_default_shortname="p"
    read -p "What is the short name of the project? []" shortprojectname
    shortprojectname=${shortprojectname:-$in_default_shortname}

    in_default_appname="myapp"
    read -p "What is the name of the first application? [$in_default_appname]" appname
    appname=${appname:-$in_default_appname}
else
    projectname=$( create_name $1 )
    projecttitle=$(create_title ${projectname})
    shortprojectname=$( create_short_name $projectname )
    appname="app"
    projectname_="${projectname//-/_}"

fi

echo "     project name: $projectname"
echo "    project title: $projecttitle"
echo "project shortname: $shortprojectname" 
echo "         app name: $appname"

if [ "$1" == "-r" ]; then
    PS3="Do you wish to rename this project?"
    select yn in Yes No
    do
        case $yn in
            Yes ) echo "Ok lets go!"; break;;
            No ) exit;;
        esac
    done
fi

export projectname
export projectname_
export projecttitle
export shortprojectname
export appname

files=( "README.adoc" "README.md" "CMakeLists.txt" "src/CMakeLists.txt" 
        "src/.tests.laplacian"  
        "src/.tests.toolbox"
        "site.yml" 
        "docs/antora.yml" 
        "package.json"
        "package-lock.json"
        "pyproject.toml"
        "docs/modules/ROOT/pages/index.adoc" 
        ".github/workflows/ci.yml" )
for i in "${files[@]}"
do
    echo "processing renaming in $i ...."
    perl -077pi.bak -e 's/feelpp-project/$ENV{'projectname'}/sg' $i
    perl -077pi.bak -e 's/feelpp_project/$ENV{'projectname_'}/sg' $i
    perl -077pi.bak -e 's/Feel\+\+ Template Project/$ENV{'projecttitle'}/sg' $i
    perl -077pi.bak -e 's/\"fp\"/"$ENV{'shortprojectname'}"/sg' $i
    perl -077pi.bak -e 's/myapp/$ENV{'appname'}/sg' $i
done
git mv src/feelpp_project src/$projectname_




