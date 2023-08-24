import os, argparse
from . import datamodel

parser = argparse.ArgumentParser()
parser.add_argument("path")
parser.add_argument("--encoding", default="binary")
args = parser.parse_args()

dm = datamodel.load(args.path)
base, extension = os.path.splitext(args.path)
out_path = base + "_converted" + extension
dm.write(out_path, args.encoding, 1)
