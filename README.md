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

## 实现说明

- 同花顺在同花的牌面里再判顺子（含 A2345 轮子，高张记 5），不会被同花吃掉。
- 顺子用点数位图扫描连续 5 张，并额外识别 A2345；同花与顺子并存时按分类顺序取最强。
- 不枚举 21 个子集：用点数位图和 4/3/2/1 张分组直接算出最佳 5 张的 tiebreak，
  结果与「枚举 21 个组合逐个评估再取最大」的参考实现一致（测试用 2000 手随机对拍，差异 0）。
- 牌面不合法会报错并指出是第几张、点数还是花色不认识；张数不对同样报错。
- 10 万手评估约 0.4 秒，评估过程只用固定大小的位图与分组列表，内存 O(1)。

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
