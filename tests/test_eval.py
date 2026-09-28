import itertools
import random
import time
import unittest

from pokereval.eval import (CATEGORIES, CardError, describe, evaluate,
                           parse_cards)


def rank(cards):
    return evaluate(parse_cards(cards))


class ParseTest(unittest.TestCase):
    def test_seven_cards(self):
        self.assertEqual(len(parse_cards("As Kh 7d 2c 3h 4d 5s")), 7)

    def test_bad_card(self):
        with self.assertRaises(CardError):
            parse_cards("As Xh")

    def test_bad_rank_reports_index(self):
        with self.assertRaises(CardError) as context:
            parse_cards("As Kh 1d Qc Js 9h 2c")
        self.assertIn("第 3 张", str(context.exception))

    def test_bad_suit_reports_index(self):
        with self.assertRaises(CardError) as context:
            parse_cards("As Kh Qx")
        self.assertIn("第 3 张", str(context.exception))

    def test_wrong_count(self):
        with self.assertRaises(CardError):
            evaluate(parse_cards("As Kh"))


class CategoryTest(unittest.TestCase):
    def test_quads(self):
        self.assertEqual(rank("As Ah Ad Ac Kd Qh 2s")[0], "quads")

    def test_quads_kicker(self):
        self.assertEqual(rank("As Ah Ad Ac Kd Qh 2s"),
                         ("quads", [14, 13]))

    def test_full_house(self):
        self.assertEqual(rank("As Ah Ad Kc Kd Qh 2s"),
                         ("full_house", [14, 13]))

    def test_full_house_picks_biggest_pair(self):
        # 三条 A + 对 K 强于三条 A + 对 Q
        strong = rank("As Ah Ad Kc Kd Qh Qs")
        weak = rank("As Ah Ad Qc Qd Kh Js")
        self.assertGreater(strong, weak)
        self.assertEqual(strong[1], [14, 13])

    def test_full_house_two_trips(self):
        # 3+3+1：三条 A + 三条 K 当葫芦 A 满 K
        self.assertEqual(rank("As Ah Ad Kc Kd Kh 2s"),
                         ("full_house", [14, 13]))

    def test_trips(self):
        self.assertEqual(rank("As Ah Ad Kc Qd Jh 2s")[0], "trips")

    def test_trips_kickers(self):
        self.assertEqual(rank("As Ah Ad Kc Qd Jh 2s"),
                         ("trips", [14, 13, 12]))

    def test_two_pair(self):
        self.assertEqual(rank("As Ah Kd Kc Qd Jh 2s"),
                         ("two_pair", [14, 13, 12]))

    def test_pair(self):
        self.assertEqual(rank("As Ah Kd Qc Jd 9h 2s"),
                         ("pair", [14, 13, 12, 11]))

    def test_high_card(self):
        self.assertEqual(rank("As Kh Qd Jc 9d 7h 2s"),
                         ("high_card", [14, 13, 12, 11, 9]))

    def test_flush(self):
        self.assertEqual(rank("As Ks Qs Js 9s 2h 3d")[0], "flush")

    def test_flush_tiebreak_top_five(self):
        # 黑桃有 6 张，取最大 5 张
        self.assertEqual(rank("As Ks Qs Js 9s 2s 3d"),
                         ("flush", [14, 13, 12, 11, 9]))


class StraightTest(unittest.TestCase):
    def test_wheel_straight(self):
        self.assertEqual(rank("As 2h 3d 4c 5s Kd Qh"),
                         ("straight", [5]))

    def test_wheel_straight_mixed_suits(self):
        result = rank("Ac 2d 3h 4s 5c Kd Qh")
        self.assertEqual(result, ("straight", [5]))

    def test_broadway_straight(self):
        # A 当最大：AKQJT
        result = rank("As Kh Qd Jc Ts 2d 3h")
        self.assertEqual(result, ("straight", [14]))

    def test_straight_flush_wheel(self):
        self.assertEqual(rank("As 2s 3s 4s 5s Kd Qh"),
                         ("straight_flush", [5]))

    def test_straight_flush_beats_flush(self):
        result = rank("9s 8s 7s 6s 5s Kd Qh")
        self.assertEqual(result[0], "straight_flush")
        self.assertEqual(result[1], [9])

    def test_flush_and_straight_strongest(self):
        # 同时存在同花（AKQJ9）和顺子（AKQJT 杂牌 T），flush 更强
        result = rank("As Ks Qs Js 9s Td 2h")
        self.assertEqual(result, ("flush", [14, 13, 12, 11, 9]))

    def test_straight_flush_in_six_flush(self):
        # 6 张黑桃里藏着 5 张同花顺子
        result = rank("As 2s 3s 4s 5s 7s Kd")
        self.assertEqual(result, ("straight_flush", [5]))


class CategoryOrderTest(unittest.TestCase):
    def test_order(self):
        self.assertEqual(CATEGORIES, (
            "high_card", "pair", "two_pair", "trips", "straight",
            "flush", "full_house", "quads", "straight_flush"))

    def test_tuple_ordering(self):
        # straight_flush > quads > full_house > flush > straight
        def value(result):
            category, tiebreak = result
            return (CATEGORIES.index(category), tiebreak)

        self.assertGreater(value(rank("As 2s 3s 4s 5s Kd Qh")),
                           value(rank("As Ah Ad Ac Kd Qh 2s")))
        self.assertGreater(value(rank("As Ah Ad Ac Kd Qh 2s")),
                           value(rank("As Ah Ad Kc Kd Qh 2s")))
        self.assertGreater(value(rank("As Ah Ad Kc Kd Qh 2s")),
                           value(rank("As Ks Qs Js 9s 2h 3d")))
        self.assertGreater(value(rank("As Ks Qs Js 9s 2h 3d")),
                           value(rank("As Kh Qd Jc Ts 2d 3h")))


class DeterminismTest(unittest.TestCase):
    def test_repeatable(self):
        text = "As 2s 3s 4s 5s Kd Qh"
        cards = parse_cards(text)
        self.assertEqual(evaluate(cards), evaluate(cards))
        self.assertEqual(describe(evaluate(cards)), describe(evaluate(cards)))


# ---- 参考实现：枚举 21 个 5 张组合，逐个独立评估，取最大 ----

REF_CATEGORY_VALUE = {name: value for value, name in enumerate(CATEGORIES)}


def ref_eval_five(cards5):
    """独立评估正好 5 张牌，返回 (类别值, tiebreak)，与主实现同一套口径。"""
    ranks = sorted((r for r, _ in cards5), reverse=True)
    count = {}
    for r in ranks:
        count[r] = count.get(r, 0) + 1
    suits = {s for _, s in cards5}
    is_flush = len(suits) == 1

    bits = 0
    for r in ranks:
        bits |= 1 << r

    def straight_high(b):
        for high in range(14, 5, -1):
            mask = 0b11111 << (high - 4)
            if b & mask == mask:
                return high
        wheel = (1 << 14) | (1 << 2) | (1 << 3) | (1 << 4) | (1 << 5)
        return 5 if b & wheel == wheel else None

    high = straight_high(bits)
    if is_flush and high is not None:
        return (REF_CATEGORY_VALUE["straight_flush"], [high])

    grouped = sorted(count.items(), key=lambda item: (-item[1], -item[0]))
    if grouped[0][1] == 4:
        kicker = max(r for r, c in grouped if c == 1)
        return (REF_CATEGORY_VALUE["quads"], [grouped[0][0], kicker])
    triples = [r for r, c in grouped if c == 3]
    pairs = sorted((r for r, c in grouped if c == 2), reverse=True)
    if triples and pairs:
        return (REF_CATEGORY_VALUE["full_house"], [triples[0], pairs[0]])
    if is_flush:
        return (REF_CATEGORY_VALUE["flush"], ranks[:5])
    if high is not None:
        return (REF_CATEGORY_VALUE["straight"], [high])
    singles = [r for r, c in grouped if c == 1]
    if triples:
        return (REF_CATEGORY_VALUE["trips"], [triples[0]] + singles[:2])
    if len(pairs) >= 2:
        return (REF_CATEGORY_VALUE["two_pair"],
                [pairs[0], pairs[1]] + singles[:1])
    if pairs:
        return (REF_CATEGORY_VALUE["pair"], [pairs[0]] + singles[:3])
    return (REF_CATEGORY_VALUE["high_card"], singles[:5])


def ref_evaluate(cards7):
    """枚举 C(7,5)=21 个组合取最强。"""
    return max(ref_eval_five(list(combo))
               for combo in itertools.combinations(cards7, 5))


def normalize(result):
    category, tiebreak = result
    return (REF_CATEGORY_VALUE[category], list(tiebreak))


def random_hand(rng):
    deck = [(rank, suit)
            for rank in range(2, 15)
            for suit in "shdc"]
    rng.shuffle(deck)
    return deck[:7]


class DifferentialTest(unittest.TestCase):
    def test_matches_enumeration_2000(self):
        rng = random.Random(20260928)
        mismatches = 0
        for _ in range(2000):
            cards = random_hand(rng)
            got = normalize(evaluate(cards))
            expected = ref_evaluate(cards)
            if got != expected:
                mismatches += 1
        self.assertEqual(mismatches, 0)


class FrequencyTest(unittest.TestCase):
    # 7 张牌（21 选 5）各牌型理论概率，Wikipedia "Poker probability"
    THEORETICAL = {
        "straight_flush": 0.0003108,
        "quads": 0.00168,
        "full_house": 0.0260,
        "flush": 0.0303,
        "straight": 0.0462,
        "trips": 0.0483,
        "two_pair": 0.235,
        "pair": 0.438,
        "high_card": 0.174,
    }

    def test_frequency_order_of_magnitude(self):
        rng = random.Random(424242)
        n = 100000
        counts = {name: 0 for name in CATEGORIES}
        for _ in range(n):
            counts[evaluate(random_hand(rng))[0]] += 1
        for name, p in self.THEORETICAL.items():
            ratio = (counts[name] / n) / p
            self.assertTrue(
                1 / 3 <= ratio <= 3,
                "%s: 实际 %.5f 理论 %.5f 比值 %.2f"
                % (name, counts[name] / n, p, ratio))


class PerformanceTest(unittest.TestCase):
    def test_100k_under_one_second(self):
        rng = random.Random(7)
        hands = [random_hand(rng) for _ in range(10000)]
        start = time.perf_counter()
        for _ in range(10):
            for cards in hands:
                evaluate(cards)
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 1.0, "10 万手耗时 %.2fs" % elapsed)


if __name__ == "__main__":
    unittest.main()
