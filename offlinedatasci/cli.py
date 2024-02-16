import argparse
from secrets import choice
import sys
from offlinedatasci import *

function_list = [download_r,download_rstudio,download_minicran,
                 download_lessons,download_python,
                 download_python_libraries]
def get_installer_functions(selection, ods_dir):
    if selection == "all":
        try_except_functions(ods_dir, function_list)
    elif selection == "rstudio":
        try_except_functions(ods_dir, download_rstudio)
    elif selection == "python":
        try_except_functions(ods_dir, download_python)
    else:
        try:
            download_function = f"download_{selection}"
            getattr(sys.modules[__name__], download_function)(ods_dir)
        except Exception:
            print(f'method does not exist for selection: {selection}')
def main():
    parser = argparse.ArgumentParser(prog = 'offlinedatasci')
    subparsers = parser.add_subparsers(help = 'sub-command help', dest='command')
    INSTALL_OPTIONS = ["all", "lessons", "minicran", "python", "python_libraries", "r", "rstudio"]

    install_parser = subparsers.add_parser('install')
    install_parser.add_argument('item',
                                default = 'all',
                                nargs = '+',
                                choices=INSTALL_OPTIONS)
    install_parser.add_argument('path',
                                 metavar = 'path',
                                 type = str,
                                 help = 'path to setup offlinedatasci files in')

    packages_parser = subparsers.add_parser('add-packages')
    packages_parser.add_argument('language',
                                nargs = 1,
                                choices =['r', 'python'])
    packages_parser.add_argument('libraries',
                                nargs = '+')
    packages_parser.add_argument('path',
                                 metavar = 'path',
                                 type = str,
                                 help = 'path to setup offlinedatasci files in')

    
    activate_parser = subparsers.add_parser('activate')
    activate_parser.add_argument('path',
                                metavar = 'path',
                                type = str,
                                help = 'path to offlinedatasci files directory')
    
    deactivate_parser = subparsers.add_parser('deactivate')

    args = parser.parse_args()

    if args.command == 'install':
        ods_dir = get_ods_dir(args.path)
        for i in args.item:
            get_installer_functions(i, ods_dir)

    elif args.command == 'add-packages':
        ods_dir = get_ods_dir(args.path)
        packages_to_install = package_selection(args.language[0], args.libraries)
        if args.language[0] == "python":
            download_python_libraries(ods_dir, packages_to_install)
        elif args.language[0] == "r":
            download_minicran(ods_dir, packages_to_install)
    elif args.command == "activate":
        ods_dir = get_ods_dir(args.path)
        activate(ods_dir)
    elif args.command == "deactivate":
        deactivate()
        
            
if __name__=='__main__':
              
    main()
