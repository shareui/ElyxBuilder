import argparse
import sys

from elyb.cmds.version import runVersion
from elyb.cmds.new import runNew
from elyb.cmds.build import runBuild
from elyb.cmds.cached import runCached
from elyb.cmds.ignore import runAddIgnore, runDelIgnore

def buildParser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="elyb")
    parser.add_argument("-v", "--version", action="store_true", help="show version")
    subparsers = parser.add_subparsers(dest="command")
    newParser = subparsers.add_parser("new", help="create new plugin from template")
    newParser.add_argument("pluginname", help="plugin name")
    newParser.add_argument("author", help="author id")
    newParser.add_argument("-zf", "--zipformat", default="eaf", help="zip format (default: eaf)")
    buildParser = subparsers.add_parser("build", help="build plugin into archive")
    buildParser.add_argument("--no-assets", action="store_true", dest="noAssets", help="exclude optionalAssets from archive")
    buildParser.add_argument("-v", "--verbose", action="store_true", dest="verbose", help="print build log")
    buildParser.add_argument("-r", "--reset", action="store_true", dest="reset", help="clear compilation cache before build (requires --compile)")
    buildParser.add_argument("-p", "--password", nargs=2, metavar=("METHOD", "PASSWORD"), dest="encrypt", help="encrypt archive (e.g. -p aes-256 mypassword)")
    buildModeGroup = buildParser.add_mutually_exclusive_group()
    buildModeGroup.add_argument("-a", "--ast", action="store_true", dest="checkAst", help="check .py files in source via AST before build")
    buildModeGroup.add_argument("-c", "--compile", action="store_true", dest="compile", help="compile .py files to .pyc and include in archive")
    subparsers.add_parser("cached", help="show which source files have changed since last compilation")
    addIgnoreParser = subparsers.add_parser("add-ignore", help="add path to an ignore list in config.yml")
    addIgnoreParser.add_argument("path", help="path to add (Unix-style)")
    addIgnoreGroup = addIgnoreParser.add_mutually_exclusive_group(required=True)
    addIgnoreGroup.add_argument("-a", "--all", action="store_const", const="all", dest="target", help="add to ignoreAll (excluded from every build)")
    addIgnoreGroup.add_argument("-na", "--no-assets", action="store_const", const="no_assets", dest="target", help="add to optionalAssets (excluded with --no-assets)")
    addIgnoreGroup.add_argument("-c", "--compile", action="store_const", const="compile", dest="target", help="add to compilationIgnore (excluded from compilation)")
    delIgnoreParser = subparsers.add_parser("del-ignore", help="remove path from an ignore list by index")
    delIgnoreParser.add_argument("index", help="index to remove")
    delIgnoreGroup = delIgnoreParser.add_mutually_exclusive_group(required=True)
    delIgnoreGroup.add_argument("-a", "--all", action="store_const", const="all", dest="target", help="remove from ignoreAll")
    delIgnoreGroup.add_argument("-na", "--no-assets", action="store_const", const="no_assets", dest="target", help="remove from optionalAssets")
    delIgnoreGroup.add_argument("-c", "--compile", action="store_const", const="compile", dest="target", help="remove from compilationIgnore")
    return parser

def main():
    parser = buildParser()
    args = parser.parse_args()
    if args.version:
        runVersion()
        return
    if args.command == "new":
        runNew(args.pluginname, args.author, args.zipformat)
        return
    if args.command == "build":
        encryptMethod, encryptPassword = (args.encrypt[0], args.encrypt[1]) if args.encrypt else (None, None)
        runBuild(args.noAssets, args.verbose, args.checkAst, args.compile, args.reset, encryptMethod, encryptPassword)
        return
    if args.command == "cached":
        runCached()
        return
    if args.command == "add-ignore":
        runAddIgnore(args.path, args.target)
        return
    if args.command == "del-ignore":
        runDelIgnore(args.index, args.target)
        return
    parser.print_help()
    sys.exit(1)
