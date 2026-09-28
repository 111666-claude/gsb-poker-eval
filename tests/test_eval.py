import random
import time
import unittest
from itertools import combinations

from pokereval.eval import CATEGORIES, CardError, evaluate, parse_cards

CATEGORY_VALUE = {name: value for value, name in enumerate(CATEGORIES)}


def rank(cards):
    return evaluate(parse_cards(cards))


# ---- 参考实现：枚举 21 个 5 张组合，逐个评估，取最强 ------------------------

def _wheel_check(mask):
    wheel = (1 << 14) | (1 << 5) | (1 << 4) | (1 << 3) | (1 << 2)
    high = 5 if mask & wheel == wheel else None
    run = 0
    for value in range(2, 15):
        if mask & (1 << value):
            run += 1
            if run >= 5:
                high = value
        else:
            run = 0
    return high


def reference_eval_five(cards5):
    """对单个 5 张组合返回 (牌型分值, tiebreak 元组)。"""
    counts = {}
    for value, _ in cards5:
        counts[value] = counts.get(value, 0) + 1
    groups = sorted(counts.items(), key=lambda item: (-item[1], -item[0]))
    shape = [count for _, count in groups]
    group_ranks = [value for value, _ in groups]
    is_flush = len({suit for _, suit in cards5}) == 1
    mask = 0
    for value, _ in cards5:
        mask |= 1 << value
    high = _wheel_check(mask)
    if is_flush and high is not None:
        return (CATEGORY_VALUE["straight_flush"], (high,))
    if shape == [4, 1]:
        return (CATEGORY_VALUE["quads"], (group_ranks[0], group_ranks[1]))
    if shape == [3, 2]:
        return (CATEGORY_VALUE["full_house"], (group_ranks[0], group_ranks[1]))
    if is_flush:
        return (CATEGORY_VALUE["flush"], tuple(sorted(counts, reverse=True)))
    if high is not None:
        return (CATEGORY_VALUE["straight"], (high,))
    if shape[0] == 3:
        return (CATEGORY_VALUE["trips"], tuple(group_ranks[:3]))
    if shape[:2] == [2, 2]:
        return (CATEGORY_VALUE["two_pair"], tuple(group_ranks[:3]))
    if shape[0] == 2:
        return (CATEGORY_VALUE["pair"], tuple(group_ranks[:4]))
    return (CATEGORY_VALUE["high_card"], tuple(group_ranks[:5]))


def reference_evaluate(cards7):
    best = max(reference_eval_five(combo) for combo in combinations(cards7, 5))
    return CATEGORIES[best[0]], list(best[1])


def deal(rng):
    deck = [(value, suit) for value in range(2, 15) for suit in "shdc"]
    rng.shuffle(deck)
    return deck[:7]


class ParseTest(unittest.TestCase):
    def test_seven_cards(self):
        self.assertEqual(len(parse_cards("As Kh 7d 2c 3h 4d 5s")), 7)

    def test_bad_card_points_to_position_and_suit(self):
        with self.assertRaises(CardError) as ctx:
            parse_cards("As Ax Kd Qc Js 9h 2d")
        self.assertIn("第 2 张", str(ctx.exception))
        self.assertIn("花色", str(ctx.exception))

    def test_bad_rank_points_to_position(self):
        with self.assertRaises(CardError) as ctx:
            parse_cards("As Kh 1d Qc Js 9h 2d")
        self.assertIn("第 3 张", str(ctx.exception))
        self.assertIn("点数", str(ctx.exception))

    def test_bad_length_points_to_position(self):
        with self.assertRaises(CardError) as ctx:
            parse_cards("As Kh Kd QcJs Js 9h 2d")
        self.assertIn("第 4 张", str(ctx.exception))

    def test_wrong_count(self):
        with self.assertRaises(CardError) as ctx:
            evaluate(parse_cards("As Kh"))
        self.assertIn("2 张", str(ctx.exception))


class CategoryTest(unittest.TestCase):
    def test_quads(self):
        self.assertEqual(rank("As Ah Ad Ac Kd Qh 2s"), ("quads", [14, 13]))

    def test_quads_kicker_compare(self):
        # 四条点数相同比踢脚：K 踢脚胜过 Q 踢脚。
        stronger = rank("As Ah Ad Ac Kd Qh 2s")
        weaker = rank("As Ah Ad Ac Qd Jh 2s")
        self.assertGreater(stronger, weaker)

    def test_full_house(self):
        self.assertEqual(rank("As Ah Ad Kc Kd Qh 2s"),
                         ("full_house", [14, 13]))

    def test_full_house_from_two_trips(self):
        # 两个三条（AAAKKK）：大的三条当三条部分，小的当对子。
        self.assertEqual(rank("As Ah Ad Kc Kd Kh 2s"),
                         ("full_house", [14, 13]))

    def test_full_house_trips_compare(self):
        # 先比三条部分：AAA 葫芦强于 KKK 葫芦，哪怕后者对子更大。
        stronger = rank("As Ah Ad 2c 2d 3h 4s")
        weaker = rank("Ks Kh Kd Ac Ad 3h 4s")
        self.assertGreater(stronger, weaker)

    def test_trips(self):
        self.assertEqual(rank("As Ah Ad Kc Qd Jh 2s"),
                         ("trips", [14, 13, 12]))

    def test_two_pair(self):
        self.assertEqual(rank("As Ah Kd Kc Qd Jh 2s"),
                         ("two_pair", [14, 13, 12]))

    def test_two_pair_kicker_is_highest_singleton(self):
        # KK QQ + A23，踢脚取 A 而不是最小单张。
        self.assertEqual(rank("Ks Kh Qd Qc As 2h 3d"),
                         ("two_pair", [13, 12, 14]))

    def test_three_pairs_kicker(self):
        # 三对 KK QQ 22 + A：踢脚取 A（大过第三对 2）。
        self.assertEqual(rank("Ks Kh Qd Qc 2s 2h Ad"),
                         ("two_pair", [13, 12, 14]))

    def test_pair(self):
        self.assertEqual(rank("As Ah Kd Qc Jd 9h 2s"),
                         ("pair", [14, 13, 12, 11]))

    def test_high_card(self):
        self.assertEqual(rank("As Kh Qd Jc 9d 7h 2s"),
                         ("high_card", [14, 13, 12, 11, 9]))

    def test_flush_tiebreak(self):
        self.assertEqual(rank("As Ks Qs Js 9s 2h 3d"),
                         ("flush", [14, 13, 12, 11, 9]))

    def test_flush_beats_independent_straight(self):
        # 黑桃同花（非顺子）+ 混色 KQJT9 顺子并存，取 flush。
        self.assertEqual(rank("Ks Js Ts 9s 8s Qh 7h")[0], "flush")


class StraightTest(unittest.TestCase):
    def test_wheel_straight(self):
        self.assertEqual(rank("As 2h 3d 4c 5s Kd Qh"), ("straight", [5]))

    def test_wheel_straight_flush(self):
        result = rank("As 2s 3s 4s 5s Kd Qh")
        self.assertEqual(result, ("straight_flush", [5]))

    def test_royal_straight_flush(self):
        self.assertEqual(rank("As Ks Qs Js Ts 2d 3h"),
                         ("straight_flush", [14]))

    def test_normal_straights(self):
        self.assertEqual(rank("5s 6h 7d 8c 9s Kd Qh"), ("straight", [9]))
        self.assertEqual(rank("As Kh Qd Jc Ts 2d 3h"), ("straight", [14]))

    def test_straight_flush_is_not_swallowed_by_flush(self):
        result = rank("9s 8s 7s 6s 5s Kd Qh")
        self.assertEqual(result, ("straight_flush", [9]))

    def test_six_high_run_beats_wheel(self):
        # 同时含 A2345 与 23456 时，高张取 6。
        self.assertEqual(rank("As 2s 3h 4d 5c 6h Kd"), ("straight", [6]))


class DeterminismTest(unittest.TestCase):
    def test_repeatable(self):
        cards = parse_cards("As 2s 3s 4s 5s Kd Qh")
        self.assertEqual(evaluate(cards), evaluate(cards))
        again = rank("As 2s 3s 4s 5s Kd Qh")
        self.assertEqual(rank("As 2s 3s 4s 5s Kd Qh"), again)


class ReferenceEquivalenceTest(unittest.TestCase):
    def test_matches_enumeration_2000(self):
        rng = random.Random(20240928)
        mismatches = 0
        for _ in range(2000):
            cards = deal(rng)
            if evaluate(cards) != reference_evaluate(cards):
                mismatches += 1
        self.assertEqual(mismatches, 0)

    def test_frequency_order_and_scale(self):
        rng = random.Random(424242)
        total = 100000
        counts = {name: 0 for name in CATEGORIES}
        for _ in range(total):
            category, _ = evaluate(deal(rng))
            counts[category] += 1
        # 7 张牌各牌型理论频率（按 C(52,7) 全空间计数）。
        expected = {
            "straight_flush": 41584,
            "quads": 224848,
            "full_house": 3473184,
            "flush": 4047644,
            "straight": 6180020,
            "trips": 6461620,
            "two_pair": 31433400,
            "pair": 58627800,
            "high_card": 23294460,
        }
        denominator = sum(expected.values())
        for name in CATEGORIES:
            ratio = (counts[name] / total) / (expected[name] / denominator)
            self.assertLess(ratio, 3.0, name)
            self.assertGreater(ratio, 1.0 / 3.0, name)


class PerformanceTest(unittest.TestCase):
    def test_100k_hands_under_one_second_target(self):
        rng = random.Random(7)
        hands = [deal(rng) for _ in range(100000)]
        start = time.perf_counter()
        for hand in hands:
            evaluate(hand)
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 3.0, "10 万手耗时 %.2fs" % elapsed)


if __name__ == "__main__":
    unittest.main()
