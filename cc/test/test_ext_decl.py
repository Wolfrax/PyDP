import pprint
import argparse
import os
import logging
#from .. import *

if __name__ == '__main__':
    global compiler

    logger = logging.getLogger(__name__)
    logging.basicConfig(encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(message)s')

    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", help="file to compile", default='')
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    parser.add_argument("-i", "--interpret", help="interpret C-code", action="store_false")
    parser.add_argument("-w", "--workingdir", help="set working directory", default=os.getcwd())
    args = parser.parse_args()

    os.chdir(args.workingdir)
    fn = args.file if args.file else ''

    CCconf.init(fn=fn, verbose=args.verbose, interpret=args.interpret)

    CCconf.compiler.pp_parser.preprocess(CCconf.compiler.file)

    # When file is preprocessed, we have all defines (which can include expression) in a list,
    # add this list to symbol table
    for c in CCconf.compiler.pp_parser.defines:
        CCconf.compiler.symbols.add(c)

    # Now parse the file
    # Note that we need to parse the include files, avoiding that it is included circularly
    for inc_file in CCconf.compiler.pp_parser.includes:
        if CCconf.compiler.pp_parser.visited(inc_file): continue  # Include file already visited
        result = CCconf.compiler.cc_parser.compile(inc_file)
        CCconf.compiler.pp_parser.set_visited(inc_file)  # Set this file to visited

    result = CCconf.compiler.cc_parser.compile(CCconf.compiler.file)
    CCconf.compiler.cc_parser.dump(CCconf.compiler.file + ".json")

    ext_decl = CCconf.compiler.cc_parser.prg.decl()
    #pprint.pprint(ext_decl)
    #CCconf.compiler.symbols.dump()

    #stmt = CCconf.compiler.cc_parser.prg.stmt()
    #pprint.pprint(stmt)



