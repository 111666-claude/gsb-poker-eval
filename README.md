# poker-eval

德州扑克 7 张牌里选最佳 5 张，只用 Python 标准库。

```
python3 -m pokereval.cli --cards 'As 2s 3s 4s 5s Kd Qh'
python3 -m pokereval.cli --cards 'As 2h 3d 4c 5s Kd Qh'
python3 -m unittest discover -s tests -v
```

## 口径（README 为准）

- **同花顺优先于同花**：`--cards 'As 2s 3s 4s 5s Kd Qh'`（五张黑桃的 5 高顺子）按口径是
  `straight_flush`，现在先判同花，给 `flush`。
- **A2345 是顺子**：`--cards 'As 2h 3d 4c 5s Kd Qh'` 按口径是 `straight`、比较点数 5，
  现在只看连续段（A、K、5、4、3、2 断成两段），给 `high_card`。
- 牌型顺序：`straight_flush` > `quads` > `full_house` > `flush` > `straight` > `trips` > `two_pair` > `pair` > `high_card`；
  比较点数按各自规则（四条比四条点数再比踢脚、两对比大对再比小对再比踢脚、葫芦比三条再比对子、同花按五张点数从大到小）。
- 判定要求：7 张牌里所有 21 种 5 张组合都要看，取最强的那个（顺子与同花都可能在 7 张里出现多次）。
- 不变量：结果与「枚举 21 个组合逐个评估再取最大」的参考实现完全一致；同一手牌重复评估结果相同。
- 规模：10 万手牌要在 1 秒内评估完，内存 O(1)；不许为每手牌构造所有 21 个子集再逐个深拷贝。

## 现在的行为

- `evaluate` 先 `if max(suits.values()) >= 5: return "flush"`，同花顺被同花吃掉。
- `_straight` 只在「排序后相邻点数差 1」的连续段里找 5 连，A2345 断成两段所以找不到。
- 没有 21 种组合的比较：直接按整手牌的点数分布定性，顺子与同花同时存在时也只认一个。

## 计划新增的能力

```
--cards 手牌   7 张牌，空格分隔，例如 'As Kh 7d'
```

## 输出

```
straight_flush tiebreak=5
```

## 目录

```
pokereval/eval.py   牌型评估
pokereval/cli.py    命令行入口
tests/              unittest 用例
```
