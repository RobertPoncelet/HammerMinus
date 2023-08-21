import os, argparse
from . import datamodel

parser = argparse.ArgumentParser()
parser.add_argument("path")
args = parser.parse_args()

dm = datamodel.load(args.path)
base, extension = os.path.splitext(args.path)
out_path = base + "_converted" + extension
dm.write("binary", 2)
