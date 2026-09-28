"""7 张牌取最佳 5 张，只用标准库。

直接在 7 张牌上推导最强 5 张（等价于枚举 21 个 5 张组合取最大），
不构造任何子集，内存 O(1)。

分类顺序：straight_flush > quads > full_house > flush > straight >
trips > two_pair > pair > high_card。A2345 记 5 高顺子。
"""

CATEGORIES = ("high_card", "pair", "two_pair", "trips", "straight",
              "flush", "full_house", "quads", "straight_flush")
RANKS = {name: value for value, name in enumerate("23456789TJQKA", start=2)}
RANK_NAMES = {value: name for name, value in RANKS.items()}
SUITS = "shdc"


class CardError(ValueError):
    """牌面不合法，带是第几张（从 1 开始）。"""

    def __init__(self, message):
        super().__init__(message)
        self.message = message


def parse_cards(text):
    """解析 "As Kh 7d" 这样的牌面，返回 [(点数, 花色), ...]。"""
    cards = []
    for index, item in enumerate(text.split(), start=1):
        if len(item) != 2:
            raise CardError("第 %d 张牌不合法（应为 点数+花色，例如 As）：%s"
                            % (index, item))
        if item[0] not in RANKS:
            raise CardError("第 %d 张牌点数不认识：%s" % (index, item))
        if item[1] not in SUITS:
            raise CardError("第 %d 张牌花色不认识：%s" % (index, item))
        cards.append((RANKS[item[0]], item[1]))
    return cards


def _straight_high(rank_bits):
    """rank_bits 第 r 位为 1 表示有点数 r；返回最高 5 连的高张，无则 None。"""
    for high in range(14, 5, -1):
        mask = 0b11111 << (high - 4)
        if rank_bits & mask == mask:
            return high
    wheel = (1 << 14) | (1 << 2) | (1 << 3) | (1 << 4) | (1 << 5)
    if rank_bits & wheel == wheel:
        return 5
    return None


def evaluate(cards):
    """返回 (牌型, 比较用的点数序列)，取 7 张里最强的 5 张。"""
    if len(cards) != 7:
        raise CardError("需要正好 7 张牌，当前是 %d 张" % len(cards))

    count_by_rank = {}
    rank_bits = 0
    suit_bits = {"s": 0, "h": 0, "d": 0, "c": 0}
    for rank, suit in cards:
        count_by_rank[rank] = count_by_rank.get(rank, 0) + 1
        rank_bits |= 1 << rank
        suit_bits[suit] |= 1 << rank

    # 同花顺：必须在同一个花色的点数集合里判顺子。
    for bits in suit_bits.values():
        high = _straight_high(bits)
        if high is not None:
            return ("straight_flush", [high])

    groups = sorted(count_by_rank.items(), key=lambda item: (-item[1], -item[0]))

    # 四条：四条点数 + 剩余 3 张里最大的踢脚。
    if groups[0][1] == 4:
        quad_rank = groups[0][0]
        kicker = max(rank for rank, _ in cards if rank != quad_rank)
        return ("quads", [quad_rank, kicker])

    # 葫芦：最大的三条 + 最大的对子。
    trips_ranks = [rank for rank, count in groups if count == 3]
    pair_ranks = sorted((rank for rank, count in groups if count == 2),
                        reverse=True)
    if trips_ranks:
        trip_rank = trips_ranks[0]
        for rank in pair_ranks:
            return ("full_house", [trip_rank, rank])
        if len(trips_ranks) >= 2:
            return ("full_house", [trip_rank, trips_ranks[1]])

    # 同花：7 张里至多一个花色能有 5 张，取该花色最大的 5 个点数。
    for bits in suit_bits.values():
        present = [rank for rank in range(14, 1, -1) if bits & (1 << rank)]
        if len(present) >= 5:
            return ("flush", present[:5])

    # 顺子：A2345 记 5。
    high = _straight_high(rank_bits)
    if high is not None:
        return ("straight", [high])

    def kickers(excluded, need):
        """按点数从大到小收集 need 个踢脚；另一组对子也可贡献一张。"""
        result = []
        for rank in sorted(count_by_rank, reverse=True):
            if rank not in excluded:
                result.append(rank)
                if len(result) == need:
                    break
        return result

    # 三条：三条点数 + 最大两张踢脚。
    if trips_ranks:
        return ("trips", [trips_ranks[0]] + kickers((trips_ranks[0],), 2))

    # 两对：大对、小对、踢脚。
    if len(pair_ranks) >= 2:
        return ("two_pair", [pair_ranks[0], pair_ranks[1]]
                + kickers((pair_ranks[0], pair_ranks[1]), 1))

    # 一对：对子点数 + 最大三张踢脚。
    if pair_ranks:
        return ("pair", [pair_ranks[0]] + kickers((pair_ranks[0],), 3))

    # 高牌：最大 5 个点数。
    return ("high_card", [rank for rank, _ in groups][:5])


def describe(result):
    """把比较用的点数序列转成可读文本。"""
    category, tiebreak = result
    return "%s tiebreak=%s" % (category, ",".join(RANK_NAMES[rank] for rank in tiebreak))
