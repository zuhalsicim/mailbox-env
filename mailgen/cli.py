"""The command line.

    python -m mailgen generate --level 2 --seed 7 --out tasks
    python -m mailgen audit --n 300
    python -m mailgen grade answer.json expected.json
"""

import argparse

from mailgen import audit, grade
from mailgen.package import write_task
from mailgen.sampler import DIAL, sample_instance


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="mailgen", description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)

    generate = commands.add_parser("generate", help="write one instance as a task directory")
    generate.add_argument("--level", type=int, choices=sorted(DIAL), required=True)
    generate.add_argument("--seed", type=int, required=True)
    generate.add_argument("--out", required=True, help="directory that receives the task directory")

    check = commands.add_parser("audit", help="check a batch of generated instances")
    check.add_argument("--n", type=int, default=300, help="number of instances, spread evenly over the levels")

    score = commands.add_parser("grade", help="grade an answer against the truth")
    score.add_argument("answer")
    score.add_argument("expected")

    args = parser.parse_args(argv)
    if args.command == "generate":
        print(write_task(sample_instance(args.level, args.seed), args.out))
        return 0
    if args.command == "audit":
        report = audit.run(args.n)
        print(audit.summary(report))
        return 0 if report["passed"] else 1
    return grade.main([args.answer, args.expected])
