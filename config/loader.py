import json
import os

def load_json(name):
    path = os.path.join("configs", f"{name}.json")
    with open(path) as f:
        return json.load(f)

def get_defaults(args):
    merged = {}
    if args.chain:
        merged.update(load_json(args.chain)["simulation"])
    if args.workload:
        merged.update(load_json(args.workload)["simulation"])
    return {k: v for k, v in merged.items() if getattr(args, k) is None}
