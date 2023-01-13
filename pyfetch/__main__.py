import argparse
import pyfetch

from pathlib import Path
from subprocess import getoutput
from pkg_resources import get_distribution

def get_version() -> str:
    if Path('.git').exists():
        return f"{get_distribution(__package__).version}-{getoutput('git rev-parse --abbrev-ref HEAD')}-{getoutput('git rev-parse --short HEAD')}"
    else:
        return get_distribution(__package__).version

def main(argv=None, in_package=None) -> None:
    if argv is None:
        in_package = True

    in_package = False if in_package is None else in_package
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--version', action='version', version=f'pyfetch v{get_version()}',
                        help='show current version and exit')
    parser.add_argument('-l', '--skip-long-commands', action='store_true',
                        help='skips commands that take awhile, removes functionality')
    args = parser.parse_args()
    
    pf = pyfetch.PyFetch(in_package, args)
    pf.main()


if __name__ == "__main__":
    main()