# AI PM Product Evaluation

synthetic offline benchmark; reviewed metrics apply only to reviewed samples

Blank metrics mean not measured, never zero or 100%.

Review evidence in each agent's results.json and complete human_review.csv.

## Business controls (no LLM)

| Metric | Result |
| --- | --- |
| scope | synthetic SQLite integration; no LLM, not enterprise production accuracy |
| risk_cases | 48 |
| tp | 10 |
| fp | 0 |
| fn | 0 |
| tn | 38 |
| risk_precision | 1.0 |
| risk_recall | 1.0 |
| risk_false_positive_rate | 0.0 |
| risk_false_negative_rate | 0.0 |
| security_cases | 12 |
| rbac_block_rate | 1.0 |
| rbac_denied_cases | 6 |
| approval_pass_cases | 2 |
| approval_reject_cases | 2 |
| unapproved_write_rate | 0.0 |
| rejected_write_rate | 0.0 |
| approved_execution_success_rate | 1.0 |
| passed | True |

## baseline_common

| Metric | Result |
| --- | --- |
| cases | 2 |
| process_contract_success_rate | 1.0 |
| reviewed_cases | 0 |
| review_coverage | 0.0 |
| reviewed_end_to_end_success_rate | NOT MEASURED |
| reviewed_end_to_end_wilson95 | NOT MEASURED |
| claims_checked | 0 |
| unsupported_claim_rate | NOT MEASURED |
| citations_checked | 0 |
| citation_correctness | NOT MEASURED |
| average_latency_ms | 7546.827999991365 |
| p95_latency_ms | 7767.519199987873 |
| usage | {"input_tokens": 3021, "output_tokens": 521, "embedding_tokens": 0, "llm_calls": 2, "embedding_calls": 0, "missing_usage": 0} |
| cost_coverage | 0.0 |
| mean_cost_cny | NOT MEASURED |
| cost_per_reviewed_success_cny | NOT MEASURED |
| timed_pairs | 0 |
| both_successful_pairs | 0 |
| paired_time_reduction | NOT MEASURED |
| time_reduction_by_trial_type | {"simulation": null, "real_user": null} |
| participants | 0 |
| paired_labor_value_saved_cny | NOT MEASURED |
| labor_value_scope | scenario estimate on both-successful timed pairs; not realized headcount savings or total ROI |
| assisted_trial_success_rate | NOT MEASURED |
| satisfaction_responses | 0 |
| mean_satisfaction_1_to_5 | NOT MEASURED |
| bad_case_counts | {} |

## workflow_common

| Metric | Result |
| --- | --- |
| cases | 2 |
| process_contract_success_rate | 1.0 |
| reviewed_cases | 0 |
| review_coverage | 0.0 |
| reviewed_end_to_end_success_rate | NOT MEASURED |
| reviewed_end_to_end_wilson95 | NOT MEASURED |
| claims_checked | 0 |
| unsupported_claim_rate | NOT MEASURED |
| citations_checked | 0 |
| citation_correctness | NOT MEASURED |
| average_latency_ms | 7308.384200005094 |
| p95_latency_ms | 9660.666499985382 |
| usage | {"input_tokens": 272, "output_tokens": 393, "embedding_tokens": 0, "llm_calls": 4, "embedding_calls": 0, "missing_usage": 0} |
| cost_coverage | 0.0 |
| mean_cost_cny | NOT MEASURED |
| cost_per_reviewed_success_cny | NOT MEASURED |
| timed_pairs | 0 |
| both_successful_pairs | 0 |
| paired_time_reduction | NOT MEASURED |
| time_reduction_by_trial_type | {"simulation": null, "real_user": null} |
| participants | 0 |
| paired_labor_value_saved_cny | NOT MEASURED |
| labor_value_scope | scenario estimate on both-successful timed pairs; not realized headcount savings or total ROI |
| assisted_trial_success_rate | NOT MEASURED |
| satisfaction_responses | 0 |
| mean_satisfaction_1_to_5 | NOT MEASURED |
| bad_case_counts | {} |

## workflow_extension

| Metric | Result |
| --- | --- |
| cases | 2 |
| process_contract_success_rate | 1.0 |
| reviewed_cases | 0 |
| review_coverage | 0.0 |
| reviewed_end_to_end_success_rate | NOT MEASURED |
| reviewed_end_to_end_wilson95 | NOT MEASURED |
| claims_checked | 0 |
| unsupported_claim_rate | NOT MEASURED |
| citations_checked | 0 |
| citation_correctness | NOT MEASURED |
| average_latency_ms | 6102.218499960145 |
| p95_latency_ms | 6334.72309994977 |
| usage | {"input_tokens": 270, "output_tokens": 198, "embedding_tokens": 0, "llm_calls": 4, "embedding_calls": 0, "missing_usage": 0} |
| cost_coverage | 0.0 |
| mean_cost_cny | NOT MEASURED |
| cost_per_reviewed_success_cny | NOT MEASURED |
| timed_pairs | 0 |
| both_successful_pairs | 0 |
| paired_time_reduction | NOT MEASURED |
| time_reduction_by_trial_type | {"simulation": null, "real_user": null} |
| participants | 0 |
| paired_labor_value_saved_cny | NOT MEASURED |
| labor_value_scope | scenario estimate on both-successful timed pairs; not realized headcount savings or total ROI |
| assisted_trial_success_rate | NOT MEASURED |
| satisfaction_responses | 0 |
| mean_satisfaction_1_to_5 | NOT MEASURED |
| bad_case_counts | {} |
