# Evidence and Language Rules

## Evidence Record

Every factual claim uses a claim-level `E###` record. A slide-level bibliography is insufficient.

Required fields:

- claim and strength
- study ID and study design
- source page and section
- table or figure when applicable
- exact excerpt
- reported numbers
- allowed wording, forbidden wording, and caveat

## Evidence Strength

- `supported`: directly reported and consistent with the study design.
- `mixed`: results differ by study, outcome, model, or condition.
- `tentative`: exploratory, marginal, underpowered, or strongly qualified.
- `not_supported`: null or contradictory result.

## Language Boundaries

### Reader-facing language

- **术语不能代替解释。** 不得把“人内共变”“因果边界”“即时情绪解释”等词单独当成结论；用完整句子交代谁发生了什么、依据是什么、不能推出什么。
- 第一次出现统计或心理学专有名词时先写白话解释。中文翻译会损失含义时，保留英文原词并在括号内解释。
- 篇幅不足时删除优先级较低的内容，不得通过删掉主语、条件或结论来压缩句子。

- Experiment: “在本实验中，诱导压力导致……”
- Observational: “压力较高的时刻与……相关/伴随出现”
- Moderation: “在该样本和模型中，关系随 X 水平而变化”
- Mediation: “结果支持一条间接统计路径”
- Null result: “未发现统计证据” rather than “没有作用”

Flag:

- all people / permanent / universal claims
- correlation written as causality
- marginal result written as significant
- AI assistance written as AI replacement
- medical or psychological treatment guarantees

## Number Rule

Every number shown in a claim must appear in the stored excerpt or an explicitly referenced table/figure. Never infer missing precision, units, sample sizes, or effect values.

## QA Pitfalls (observed)

- `hls_academic/qa.build_language_report` 对每条 slide 的 **整段 JSON 字符串**做 forbidden_wording 子串匹配，**不识别否定**。例如在边界声明里写「不是大样本问卷，而是 16 人的深度叙事」会被命中「E002 禁止措辞·大样本」；写「不等于'所有中国留学生都如此'」会被命中「E003 禁止措辞·所有中国留学生都如此」。绕开方式：边界声明里避开 forbidden 字面，改用同义但不同的表述（例：「不是抽样调查」「不能推及'每一位中国留学生'」「不等于对中国留学生群体的总体描述」）。
- `scripts/build_qa_reports.py --manifest` 必须传 `output/render-manifest.json`（由 `screenshot.mjs` 写出，含 `slide_count` + `files`），不能传 `work/source-assets.json`（只有 `asset_count` + `assets`），否则 visual report 会误报「DOM slide count and screenshot manifest count differ」+「PNG files checked: 0」。
