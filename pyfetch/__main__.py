import argparse
import pyfetch

def main(argv=None, in_package=None) -> None:
    if argv is None:
        in_package = True

    in_package = False if in_package is None else in_package
    
    parser = argparse.ArgumentParser()
    #parser.add_argument('-s', '--semi-tether', action='store_true',
    #                    help="semi-tether a tethered install")
    #parser.add_argument('-v', '--version', action='version', version=f'pyfetch v{utils.get_version()}',
    #                    help='show current version and exit')
    args = parser.parse_args()
    
    pf = pyfetch.PyFetch(in_package, args)
    pf.main()


if __name__ == "__main__":
    main()