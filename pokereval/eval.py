"""7 张牌取最佳 5 张，只用标准库。

缺陷：先判同花再判顺子（同花顺被报成同花），顺子只看连续段（不认 A2345），
也没做「7 选 5 取最优」的组合比较。
"""

CATEGORIES = ("high_card", "pair", "two_pair", "trips", "straight",
              "flush", "full_house", "quads", "straight_flush")
RANKS = {name: value for value, name in enumerate("23456789TJQKA", start=2)}
RANK_NAMES = {value: name for name, value in RANKS.items()}
SUITS = "shdc"


class CardError(ValueError):
    """牌面不合法。缺陷：不带是第几张。"""

    def __init__(self, message):
        super().__init__(message)
        self.message = message


def parse_cards(text):
    """解析 "As Kh 7d" 这样的牌面。"""
    cards = []
    for item in text.split():
        if len(item) != 2 or item[0] not in RANKS or item[1] not in SUITS:
            raise CardError("牌面不合法：%s" % item)
        cards.append((RANKS[item[0]], item[1]))
    return cards


def _straight(ranks):
    """缺陷：只看连续段，不认 A2345，也不区分同花。"""
    unique = sorted(set(ranks), reverse=True)
    run = 1
    for index in range(1, len(unique)):
        if unique[index - 1] - 1 == unique[index]:
            run += 1
            if run >= 5:
                return unique[index - 4]
        else:
            run = 1
    return None


def evaluate(cards):
    """返回 (牌型, 比较用的点数序列)。缺陷：分类顺序错、A2345 不认。"""
    if len(cards) != 7:
        raise CardError("需要正好 7 张牌")
    counts = {}
    for rank, _ in cards:
        counts[rank] = counts.get(rank, 0) + 1
    ordered = sorted(counts.items(), key=lambda item: (-item[1], -item[0]))
    shape = [count for _, count in ordered]
    ranks = [rank for rank, _ in ordered]
    suits = {}
    for _, suit in cards:
        suits[suit] = suits.get(suit, 0) + 1
    if max(suits.values()) >= 5:
        return ("flush", ranks[:5])  # 缺陷：同花顺也走到这里
    high = _straight(ranks)
    if high is not None:
        return ("straight", [high])
    if shape[:1] == [4]:
        return ("quads", ranks[:2])
    if shape[:2] == [3, 2]:
        return ("full_house", ranks[:2])
    if shape[:1] == [3]:
        return ("trips", ranks[:3])
    if shape[:2] == [2, 2]:
        return ("two_pair", ranks[:3])
    if shape[:1] == [2]:
        return ("pair", ranks[:4])
    return ("high_card", ranks[:5])


def describe(result):
    """把比较用的点数序列转成可读文本。"""
    category, tiebreak = result
    return "%s tiebreak=%s" % (category, ",".join(RANK_NAMES[rank] for rank in tiebreak))
