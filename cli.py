import argparse
import os
from RPM import RytonPackageManager

def main():
    parser = argparse.ArgumentParser(description='Ryton Package Manager')
    
    parser.add_argument('command', choices=['install', 'remove', 'list', 'github'])
    parser.add_argument('package', nargs='?', help='package name or github repo')
    parser.add_argument('--source', '--type', choices=['ryton', 'python', 'zig'],
                       default='ryton', help='package source type')
    
    args = parser.parse_args()
    
    pm = RytonPackageManager(os.getcwd())
    
    if args.command == 'github':
        pm.install_from_github(args.package, args.source)
    elif args.command == 'install':
        pm.install(args.package, args.source)
    elif args.command == 'remove':
        pm.remove(args.package, args.source)
    elif args.command == 'list':
        pm.list_packages(args.source)

if __name__ == '__main__':
    main()

