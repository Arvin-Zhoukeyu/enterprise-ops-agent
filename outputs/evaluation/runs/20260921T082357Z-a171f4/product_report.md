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
| cases | 60 |
| process_contract_success_rate | 0.95 |
| reviewed_cases | 0 |
| review_coverage | 0.0 |
| reviewed_end_to_end_success_rate | NOT MEASURED |
| reviewed_end_to_end_wilson95 | NOT MEASURED |
| claims_checked | 0 |
| unsupported_claim_rate | NOT MEASURED |
| citations_checked | 0 |
| citation_correctness | NOT MEASURED |
| average_latency_ms | 7071.402820002792 |
| p95_latency_ms | 15260.684699984267 |
| usage | {"input_tokens": 191362, "output_tokens": 14516, "embedding_tokens": 0, "llm_calls": 112, "embedding_calls": 0, "missing_usage": 0} |
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
| bad_case_counts | {"arguments": 3} |

## workflow_common

| Metric | Result |
| --- | --- |
| cases | 60 |
| process_contract_success_rate | 0.9 |
| reviewed_cases | 0 |
| review_coverage | 0.0 |
| reviewed_end_to_end_success_rate | NOT MEASURED |
| reviewed_end_to_end_wilson95 | NOT MEASURED |
| claims_checked | 0 |
| unsupported_claim_rate | NOT MEASURED |
| citations_checked | 0 |
| citation_correctness | NOT MEASURED |
| average_latency_ms | 32626.379048331484 |
| p95_latency_ms | 35325.24710003054 |
| usage | {"input_tokens": 153586, "output_tokens": 27428, "embedding_tokens": 44, "llm_calls": 228, "embedding_calls": 1, "missing_usage": 0} |
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
| bad_case_counts | {"insufficient_evidence": 4, "tool_selection": 3, "arguments": 1} |

## workflow_extension

| Metric | Result |
| --- | --- |
| cases | 30 |
| process_contract_success_rate | 0.6666666666666666 |
| reviewed_cases | 0 |
| review_coverage | 0.0 |
| reviewed_end_to_end_success_rate | NOT MEASURED |
| reviewed_end_to_end_wilson95 | NOT MEASURED |
| claims_checked | 0 |
| unsupported_claim_rate | NOT MEASURED |
| citations_checked | 0 |
| citation_correctness | NOT MEASURED |
| average_latency_ms | 18778.469953334814 |
| p95_latency_ms | 42367.55700001959 |
| usage | {"input_tokens": 118023, "output_tokens": 17287, "embedding_tokens": 123, "llm_calls": 114, "embedding_calls": 12, "missing_usage": 0} |
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
| bad_case_counts | {"routing": 3, "tool_selection": 9, "insufficient_evidence": 4, "security": 1} |
