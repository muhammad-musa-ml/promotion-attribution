import argparse

from .evaluate import run_seeds, summary, write_results

GENERATOR = dict(users=2000, jobs=30, promoted=10, considered=3)


def main():
    p = argparse.ArgumentParser(prog="promoattr")
    sub = p.add_subparsers(dest="command", required=True)
    one = sub.add_parser("run", help="print the results for one seed")
    one.add_argument("--seed", type=int, default=7)
    rep = sub.add_parser("report", help="run seeds 1..N and write results/")
    rep.add_argument("--seeds", type=int, default=10)
    rep.add_argument("--out", default="results")
    args = p.parse_args()

    if args.command == "run":
        runs = run_seeds([args.seed], **GENERATOR)
        print(summary(runs, GENERATOR))
    else:
        runs = run_seeds(range(1, args.seeds + 1), **GENERATOR)
        write_results(runs, GENERATOR, args.out)
        print(f"wrote {args.out}/summary.md and {args.out}/by_seed.csv for {args.seeds} seeds")


if __name__ == "__main__":
    main()
