# Creative Fatigue Management Playbook

一套面向电商广告投放的素材衰退管理方法论和计算模板，适合 Meta Ads、TikTok Ads、Google Ads Demand Gen / PMax 的素材日报、周报和素材库管理。

## 核心结论

素材衰退不要只按“上线多少天”判断。更稳的做法是把素材当成一个组合来管理，同时看：

| 模块 | 指标 | 用途 |
|---|---|---|
| 年龄结构 | GMV 加权日龄、花费加权日龄、曝光加权日龄 | 判断成交、预算、曝光是否被老素材撑住 |
| 曝光疲劳 | Frequency、Reach 增速、daily new users | 判断是否出现重复曝光压力 |
| 表现衰减 | 近 3 日 vs 近 7 日 ROAS、CPA、CTR、CVR | 判断是否真的效率下降 |
| 集中风险 | Top1 GMV 占比、Top3 GMV 占比、HHI、有效素材数 | 判断是否过度依赖少数爆款 |
| 补给能力 | 每周新增素材数、通过测试素材数、可替换素材库存天数 | 判断未来 7-14 天有没有素材接力 |

## 快速使用

1. 安装依赖：

```bash
python3 -m pip install -r requirements.txt
```

2. 按模板准备素材日报：

```bash
cp templates/creative_daily_template.csv data_raw/creative_daily.csv
```

3. 运行计算：

```bash
python3 scripts/calc_creative_fatigue.py \
  --input data_raw/creative_daily.csv \
  --output-dir output \
  --target-roas 1.5
```

4. 查看输出：

| 文件 | 说明 |
|---|---|
| `output/creative_scores.csv` | 每条素材的表现、衰退指标和建议动作 |
| `output/portfolio_metrics.csv` | 账户/素材组合层面的集中度、加权日龄和有效素材数 |
| `output/error_rows.csv` | 字段缺失、日期异常等无法计算的行，不会被静默删除 |

也可以先跑样例：

```bash
python3 scripts/calc_creative_fatigue.py \
  --input sample_data/creative_daily_sample.csv \
  --output-dir output \
  --target-roas 1.5
```

## 关键公式

```text
GMV 加权日龄 = SUM(日龄_i * GMV_i) / SUM(GMV_i)
花费加权日龄 = SUM(日龄_i * Spend_i) / SUM(Spend_i)
曝光加权日龄 = SUM(日龄_i * Impressions_i) / SUM(Impressions_i)

Top1 GMV 占比 = Top1 GMV / 总 GMV
Top3 GMV 占比 = Top3 GMV 之和 / 总 GMV
HHI = SUM(每条素材 GMV 占比 ^ 2)
有效素材数 = 1 / HHI

ROAS 衰减率 = 近 3 日 ROAS / 近 7 日 ROAS - 1
CTR 衰减率 = 近 3 日 CTR / 近 7 日 CTR - 1
CPA 上升率 = 近 3 日 CPA / 近 7 日 CPA - 1
```

## 动作规则

| 等级 | 触发条件 | 动作 |
|---|---|---|
| 黄色 | Top3 GMV 占比 > 60% 或 Top1 GMV 占比 > 30% | 准备同角度变体，先补素材，不要直接替换赢家 |
| 橙色 | Frequency >= 2.5 且 ROAS 衰减率 <= -20% | 刷新 hook、封面、前三秒、达人剪辑版本 |
| 红色 | CTR 下滑 >= 20%，CPA 上升 >= 20%，ROAS 低于目标 | 降预算或暂停，复查样本量、归因和落地页 |
| 黑色 | Top3 同时下滑且没有测试通过的新素材 | 停止放量，集中补素材库存 |

阈值不是平台通用真理，建议按品类、客单价、转化周期、预算和归因窗口校准。

## 项目结构

```text
.
├── docs/
│   ├── methodology.md
│   ├── optimizer-review.md
│   └── platform-notes.md
├── scripts/
│   └── calc_creative_fatigue.py
├── templates/
│   ├── action_rules.csv
│   └── creative_daily_template.csv
├── sample_data/
│   └── creative_daily_sample.csv
├── data_raw/
├── data_processed/
└── output/
```

## 重要说明

- 不要只用日龄判断疲劳。老素材可能仍然健康，新素材也可能很快衰退。
- 不要只看 GMV 加权日龄。花费高但 GMV 下降的素材，会被 GMV 权重低估风险。
- 不要直接删除 Google PMax / Demand Gen 的低评分资产。更稳妥的方式是先补新素材，再逐步替换。
- 对 Meta 和 TikTok，素材刷新更适合“加入新素材到已有稳定结构”，但仍要结合学习期、预算和样本量。

## 参考来源

- Meta Analytics: [Creative Fatigue: How advertisers can improve performance by managing repeated exposures](https://medium.com/%40AnalyticsAtMeta/creative-fatigue-how-advertisers-can-improve-performance-by-managing-repeated-exposures-e76a0ea1084d)
- TikTok Ads Help: [Creative best practices for performance ads](https://ads.tiktok.com/help/article/creative-best-practices?lang=en)
- Google Ads Help: [Demand Gen creative assets refresh guidance](https://support.google.com/google-ads/answer/17025280?hl=en)
- Google Ads Help: [Best practices for Performance Max creative assets](https://support.google.com/google-ads/answer/14528221?hl=en)
- Google Ads Help: [About asset group reporting for Performance Max](https://support.google.com/google-ads/answer/13872527?hl=en)
