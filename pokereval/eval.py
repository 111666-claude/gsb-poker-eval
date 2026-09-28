"""7 张牌取最佳 5 张，只用标准库。

按 README 口径直接分析整手牌取最优（等价于枚举 21 个 5 张组合再取最大）：
同花顺先于同花判定，A2345 记 5 高顺子，内存 O(1)，不构造任何子集。
"""

CATEGORIES = ("high_card", "pair", "two_pair", "trips", "straight",
              "flush", "full_house", "quads", "straight_flush")
RANKS = {name: value for value, name in enumerate("23456789TJQKA", start=2)}
RANK_NAMES = {value: name for name, value in RANKS.items()}
SUITS = "shdc"

WHEEL_RUN = (1 << 14) | 0b111100  # A 2 3 4 5（bits 14,5,4,3,2），A 当 1


class CardError(ValueError):
    """牌面不合法，错误信息会指出是第几张、点数还是花色的问题。"""

    def __init__(self, message):
        super().__init__(message)
        self.message = message


def parse_cards(text):
    """解析 "As Kh 7d" 这样的牌面，返回 [(点数, 花色), ...]。"""
    cards = []
    for index, item in enumerate(text.split(), start=1):
        if len(item) != 2:
            raise CardError("第 %d 张牌不合法：%r" % (index, item))
        rank, suit = item[0], item[1]
        if rank not in RANKS:
            raise CardError("第 %d 张牌点数不认识：%r" % (index, item))
        if suit not in SUITS:
            raise CardError("第 %d 张牌花色不认识：%r" % (index, item))
        cards.append((RANKS[rank], suit))
    return cards


def _straight_high(mask):
    """在点数位图（bit2..bit14）上找最高顺子高张；A2345 返回 5，无顺子返回 None。"""
    if mask & WHEEL_RUN == WHEEL_RUN:
        high = 5
    else:
        high = None
    run = 0
    for rank in range(2, 15):
        if mask & (1 << rank):
            run += 1
            if run >= 5 and rank > (high or 0):
                high = rank
        else:
            run = 0
    return high


def evaluate(cards):
    """评估 7 张牌，返回 (牌型, 比较用的点数序列)。

    tiebreak 即最佳 5 张所用点数：顺子只存高张（A2345 存 5）；
    同花/高牌按从大到小五张；其余按四条点+踢脚、三条+对等规则。
    """
    if len(cards) != 7:
        raise CardError("需要正好 7 张牌，当前 %d 张" % len(cards))

    rank_mask = 0
    flush_masks = {suit: 0 for suit in SUITS}
    for rank, suit in cards:
        rank_mask |= 1 << rank
        flush_masks[suit] |= 1 << rank

    quads = []
    trips = []
    pairs = []
    singles = []
    for rank in range(14, 1, -1):
        count = 0
        bit = 1 << rank
        for suit in SUITS:
            if flush_masks[suit] & bit:
                count += 1
        if count == 4:
            quads.append(rank)
        elif count == 3:
            trips.append(rank)
        elif count == 2:
            pairs.append(rank)
        elif count == 1:
            singles.append(rank)

    flush_suit = None
    for suit in SUITS:
        if bin(flush_masks[suit]).count("1") >= 5:
            flush_suit = suit
            break

    # straight_flush / flush：同一种花色超过 5 张时，最佳 5 张就是其中最大的顺子/最大五张。
    if flush_suit is not None:
        high = _straight_high(flush_masks[flush_suit])
        if high is not None:
            return ("straight_flush", [high])
        flush_tiebreak = []
        for rank in range(14, 1, -1):
            if flush_masks[flush_suit] & (1 << rank):
                flush_tiebreak.append(rank)
                if len(flush_tiebreak) == 5:
                    break
        return ("flush", flush_tiebreak)

    # quads：四条点数 + 剩余牌里最大的踢脚。
    if quads:
        kicker = max(rank for rank in range(14, 1, -1)
                     if rank != quads[0] and rank_mask & (1 << rank))
        return ("quads", [quads[0], kicker])

    # full_house：一个三条 + 一个对子；没有对子时，两个三条取大的当对子。
    if trips:
        if pairs:
            return ("full_house", [trips[0], pairs[0]])
        if len(trips) >= 2:
            return ("full_house", [trips[0], trips[1]])

    # straight：用全部 7 张找最高顺子。
    high = _straight_high(rank_mask)
    if high is not None:
        return ("straight", [high])

    # trips：三条点数 + 两个最大踢脚。
    if trips:
        return ("trips", [trips[0], singles[0], singles[1]])

    # two_pair：两大对 + 最大踢脚。
    if len(pairs) >= 2:
        kicker_rank = pairs[2] if len(pairs) == 3 and pairs[2] > singles[0] else singles[0]
        return ("two_pair", [pairs[0], pairs[1], kicker_rank])

    # pair：对子点数 + 三个最大踢脚。
    if pairs:
        return ("pair", [pairs[0], singles[0], singles[1], singles[2]])

    return ("high_card", singles[:5])


def describe(result):
    """把比较用的点数序列转成可读文本。"""
    category, tiebreak = result
    return "%s tiebreak=%s" % (category, ",".join(RANK_NAMES[rank] for rank in tiebreak))
