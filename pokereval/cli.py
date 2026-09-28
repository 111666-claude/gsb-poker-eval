"""命令行入口：评估一手 7 张牌。"""

import argparse
import sys

from .eval import CardError, describe, evaluate, parse_cards


def build_parser():
    parser = argparse.ArgumentParser(prog="poker-eval", description="7 选 5 牌型评估")
    parser.add_argument("--cards", help="7 张牌，例如 'As 2s 3s 4s 5s Kd Qh'")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if not args.cards:
        print("错误：需要 --cards", file=sys.stderr)
        return 2
    try:
        cards = parse_cards(args.cards)
        print(describe(evaluate(cards)))
    except CardError as error:
        print("错误：%s" % error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
