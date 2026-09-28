import unittest

from pokereval.eval import CardError, evaluate, parse_cards


def rank(cards):
    return evaluate(parse_cards(cards))


class ParseTest(unittest.TestCase):
    def test_seven_cards(self):
        self.assertEqual(len(parse_cards("As Kh 7d 2c 3h 4d 5s")), 7)

    def test_bad_card(self):
        with self.assertRaises(CardError):
            parse_cards("As Xh")

    def test_wrong_count(self):
        with self.assertRaises(CardError):
            evaluate(parse_cards("As Kh"))


class CategoryTest(unittest.TestCase):
    def test_quads(self):
        self.assertEqual(rank("As Ah Ad Ac Kd Qh 2s")[0], "quads")

    def test_full_house(self):
        self.assertEqual(rank("As Ah Ad Kc Kd Qh 2s")[0], "full_house")

    def test_trips(self):
        self.assertEqual(rank("As Ah Ad Kc Qd Jh 2s")[0], "trips")

    def test_two_pair(self):
        self.assertEqual(rank("As Ah Kd Kc Qd Jh 2s")[0], "two_pair")

    def test_pair(self):
        self.assertEqual(rank("As Ah Kd Qc Jd 9h 2s")[0], "pair")

    def test_high_card(self):
        self.assertEqual(rank("As Kh Qd Jc 9d 7h 2s")[0], "high_card")

    def test_flush(self):
        self.assertEqual(rank("As Ks Qs Js 9s 2h 3d")[0], "flush")


if __name__ == "__main__":
    unittest.main()
