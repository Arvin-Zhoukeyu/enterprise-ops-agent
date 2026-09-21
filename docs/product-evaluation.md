# AI PM 项目评测与结果记录

本项目使用合成采购数据。离线组件测试、模型任务测试、人工实验分别报告，不能合并成企业生产准确率。

## 运行方式

在项目目录执行。Docker 环境下，在下列每条 `python` 命令前加 `docker compose run --rm api`。

```bash
# 不调用模型，不连接业务数据库。运行48条风险规则、12条审批集成案例。
python -m scripts.run_evaluation --suite business

# 先在已初始化的业务数据库上做少量在线测试，确认百炼能调用。
python -m scripts.run_evaluation --suite all --limit 2

# 完整评测：两条 Agent 使用相同60条公共案例，另有30条Workflow扩展、20条RAG案例。
python -m scripts.run_evaluation
```

运行在线评测前，需要初始化 PostgreSQL 并配置百炼 Key。升级到规则2026.2后执行一次：

```bash
python -m scripts.build_knowledge_base
```

索引使用规则版本后缀，防止加载旧政策。原有数据库无需重新seed；seed会清理数据，不是评测步骤。
风险历史按当前被评估交付发生日期向前六个日历月统计，排除当前订单、同日及之后事件；金额与延期最小阈值均含边界。
这是一项回溯筛选，非未来风险预测，也不会计算未交付订单的实时延期风险。

## 结果位置

每次运行产生独立 `outputs/evaluation/runs/<run_id>/`，不会覆盖旧结果。
`outputs/evaluation/latest_run.txt` 记录最近的运行目录。

- `summary.json`：总报告、模型名、代码指纹、数据集指纹、运行范围。
- `dataset.json`：本次使用的案例快照，--limit时只保留抽取的在线案例。
- `product_report.md`：可阅读的产品指标报告。
- `product_metrics.json`：产品指标及分母、覆盖率。
- `business_results.json`：规则TP/FP/FN/TN及真实审批图、隔离SQLite写入结果。
- 各Agent的`results.json`：问题、回答、工具结果、参数和Token，是人工审核的证据。
- `human_review.csv`：待填写的人工审核与配对耗时记录。
- `bad_cases.json`：路由、工具、参数、安全、证据、答案等错误分类。

数据集共有170条唯一案例：110条自然语言/检索案例加60条组件案例，不能宣称170条都调用了大模型。
目前这些是开发回归集；调Prompt后在这套数据上的成绩不等于独立保留测试集或真实用户泛化能力。

## 计费与成本

将`evaluation/prices.example.json`复制为自己使用的价格配置，三个null替换为百炼控制台对应模型的人民币/百万Token价格。
配置可以额外包含`hourly_labor_cny`作为人工时薪假设。不要直接使用网上示例价格。

```bash
python -m scripts.run_evaluation --prices evaluation/prices.json
```

Baseline和Workflow都采集Chat和在线RAG Embedding用量。成本是按填写费率估算，不是实际账单；不含服务器、建库、人工审批和没有返回usage的重试成本。缺费率/usage或请求出错时成本留空并显示覆盖率。缓存、阶梯计费需自行调整费率或对照账单。
每成功任务成本仅在全部任务已审核且成本完整时，使用全部请求成本除以成功任务数，失败请求不会被免费忽略。
人工价值仅按配对实验时间差和时薪估算；不等于裁员收益或完整项目ROI。

## 人工审核和用户测试

打开本次`human_review.csv`，保留agent和id，按证据填写以下列。空白是未测，不是失败或成功。

| 列 | 填写要求 |
| --- | --- |
| reviewer | 审核者编号 |
| task_achieved | 1或0：业务结果、事实、要求的政策引用及执行结果整体是否正确 |
| claims_checked / unsupported_claims | 检查事实数 / 无证据事实数，两列一起填写 |
| citations_checked / correct_citations | 检查引用数 / 来源和内容均正确的引用数 |
| participant | 实际参与测试者的匿名编号 |
| trial_type | simulation或real_user，模拟实验与真实用户分开报告 |
| human_seconds | 同一任务纯人工完成总耗时 |
| assisted_seconds | Agent辅助下总耗时，包含输入、等待、阅读、复核和修正 |
| human_success / assisted_success | 两种方式是否成功，各填1或0 |
| satisfaction | 实际反馈的1～5分 |
| feedback | 错误、原因及改进建议 |

先选择同样难度的任务，交替两种方式的先后顺序，避免熟悉答案导致虚假提效。按相同规则核验结果。时间降低率只比较两边均成功的样本，同时报告总配对数、成功样本数、参与人数和辅助任务成功率；失败任务不能悄悄被隐藏。
批准建单的成功必须验证工单实际存在；“等审批”只算完成等待审批这一子任务，不能标为完成整条业务流程。组件套件实际测试通过/拒绝后写入，但在线Agent现有评测停在审批点，不会自动替你批准真实数据库写入。
对找不到的记录应明确未找到；对于部分证据，不得编造确定结论。引用正确需检查具体政策条款，不是只出现文件名。

填完后不必重新调用模型：

```bash
python -m scripts.run_evaluation --report-only outputs/evaluation/runs/实际run_id --prices evaluation/prices.json
```

刷新产品报告得到审核覆盖率、审核样本端到端成功率、95% Wilson区间、无依据事实比例、引用正确率、配对耗时降低、满意度、成本等。区间只反映样本数，不解决合成样本代表性问题。
旧的`task_completion_accuracy`保留兼容性，其含义是流程契约检查；产品报告中的`reviewed_end_to_end_success_rate`才包含人工业务结果审核。

## 改进前后对比

```bash
python -m scripts.run_evaluation --report-only outputs/evaluation/runs/新run_id --compare-to outputs/evaluation/runs/旧run_id
```

数据集指纹和案例ID必须相同。`comparison.json`列出修复与回退案例；不同模型、规则、知识库或业务数据库快照也可能导致变化，应结合运行元数据解释，不能直接归因于Prompt优化。
建议保留至少3个Bad Case的“现象、原因、修改、回归结果”，作为面试中持续迭代的证据。
