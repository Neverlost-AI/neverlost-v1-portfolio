"""Local proof command: python -B -m engine.runtime.runner case_001."""
import argparse
import json
from .adapter import execute

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("case_id")
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args()
    result = execute(args.case_id)
    print(json.dumps(result if args.full else {
        key: result[key] for key in ["run_id", "case_id", "status", "engine", "counts", "result_sha256"]
    }, indent=2))

if __name__ == "__main__":
    main()
