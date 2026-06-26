# 平台口径与操作注意事项

## Meta Ads

Meta Analytics 对 creative fatigue 的核心定义是：用户反复看到同一创意元素后，响应率下降，CPA 上升。一个关键点是，疲劳应该尽量在“素材/创意元素”层面理解，而不是只看 campaign、ad set 或 ad 的 frequency。

落地建议：

| 场景 | 建议 |
|---|---|
| ASC / Broad 主力素材跑量 | 不要一掉 ROAS 就直接关，先看近 3/7 日衰减和频次 |
| Top3 GMV 占比高 | 保留赢家，同时做同角度变体 |
| CTR 下滑但 CVR 稳定 | 优先改 hook、封面、前 3 秒、首屏字幕 |
| CTR 稳定但 CVR 下滑 | 查落地页、优惠、库存、价格、评论和站点速度 |
| 多广告共用类似素材 | 要按 creative_id / 素材相似度汇总，不要只看单个 ad |

## TikTok Ads

TikTok 官方建议持续测试学习，并在投放结果持续下降或 daily new users 偏低时刷新素材。刷新时，官方更推荐把新素材加入现有 ad group 来延长生命周期，而不是每次都新建 ad group。

落地建议：

| 场景 | 建议 |
|---|---|
| 视频观看和 CTR 同时下降 | 换前三秒、节奏、字幕密度 |
| daily new users 偏低 | 补新素材或扩大受众 |
| 同质化 UGC 太多 | 换达人、场景、叙事结构 |
| 起量素材快衰退 | 复制其结构，但改变视觉和开头冲突点 |

TikTok 更适合高频素材供给，素材库要按 hook、达人、场景、节奏、CTA 管理。

## Google Demand Gen

Google 对 Demand Gen 的建议更强调稳定替换：

- 先添加新素材，再删除旧素材；
- 对 evergreen campaign 只做小比例、渐进式素材更换；
- 保留 top-performing assets；
- 素材至少经历约 14 天 ramp-up，再判断是否真的低效。

落地建议：

| 场景 | 建议 |
|---|---|
| 常青 campaign 表现稳定 | 小比例加入新素材，不要大规模换血 |
| 新素材促销活动 | 提前进入审核和学习，不要临近大促才上线 |
| 大量新素材测试 | 先在测试 campaign 里跑，再逐步并入常青 campaign |

## Google Performance Max

PMax 的资产报告和组合报告很重要，但 Google 也提示不要仅因为某个 asset group CPA 高或 ROAS 低就简单删除，因为它仍可能对整体目标有边际贡献。

落地建议：

| 场景 | 建议 |
|---|---|
| low rating asset | 不要裸删，先补新素材替换 |
| 资产组合单一 | 增加图片、视频、标题、描述和附加信息 |
| 需要看组合表现 | 用 Asset group details 和 Combinations report |
| PMax 与 Search/Shopping 抢量 | 同时看搜索词承接、品牌词占比和转化价值口径 |

## 参考来源

- Meta Analytics: https://medium.com/%40AnalyticsAtMeta/creative-fatigue-how-advertisers-can-improve-performance-by-managing-repeated-exposures-e76a0ea1084d
- TikTok Ads Help: https://ads.tiktok.com/help/article/creative-best-practices?lang=en
- Google Demand Gen: https://support.google.com/google-ads/answer/17025280?hl=en
- Google PMax creative assets: https://support.google.com/google-ads/answer/14528221?hl=en
- Google PMax asset group reporting: https://support.google.com/google-ads/answer/13872527?hl=en
