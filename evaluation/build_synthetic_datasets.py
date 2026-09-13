import json
from pathlib import Path
from typing import Any


DATASET_PATH = Path("evaluation/dataset.json")


def write_dataset(dataset: dict[str, Any]) -> None:
    DATASET_PATH.write_text(
        json.dumps(dataset, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        "Wrote 110 synthetic cases to "
        f"{DATASET_PATH}"
    )


def baseline_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []

    def add(
        category: str,
        query: str,
        routing: str,
        tool: str | None = None,
        arguments: dict[str, Any] | None = None,
        status: str | None = None,
    ) -> None:
        case = {
            "id": f"EB{len(cases) + 1:03d}",
            "source": "synthetic",
            "category": category,
            "query": query,
            "expected_routing": routing,
            "expected_tool": tool,
            "expected_arguments": arguments or {},
        }
        if status is not None:
            case["expected_status"] = status
        cases.append(case)

    general_queries = [
        "什么是供应链风险？",
        "采购订单通常包含哪些信息？",
        "供应商评级有什么作用？",
        "什么是交付延期风险？",
        "企业为什么要管理供应商风险？",
        "什么是采购合规？",
        "如何理解风险事件的严重等级？",
        "风险工单在企业运营中有什么作用？",
    ]
    for query in general_queries:
        add("general_knowledge", query, "DIRECT_RESPONSE")

    supplier_queries = [
        ("查询供应商 SUP-2026-0001", "SUP-2026-0001"),
        ("帮我看一下 SUP-2026-0003 的详细信息", "SUP-2026-0003"),
        ("SUP-2026-0007 的风险等级是多少？", "SUP-2026-0007"),
        ("供应商 SUP-2026-0012 来自哪个国家？", "SUP-2026-0012"),
        ("检索供应商编号 SUP-2026-0018", "SUP-2026-0018"),
        ("查看 SUP-2026-0021 的评级与状态", "SUP-2026-0021"),
        ("请返回 SUP-2026-0031 的供应商档案", "SUP-2026-0031"),
        ("查询 SUP-2026-0040 的合作信息", "SUP-2026-0040"),
        ("Do we have details for supplier SUP-2026-0050?", "SUP-2026-0050"),
        ("查一下不存在的供应商 SUP-2026-9999", "SUP-2026-9999"),
    ]
    for query, code in supplier_queries:
        add("supplier_lookup", query, "TOOL_CALL", "get_supplier", {"supplier_code": code})

    supplier_filters = [
        ("列出5个高风险供应商", "high", 5),
        ("给我10个低风险供应商", "low", 10),
        ("查询8个中风险供应商", "medium", 8),
        ("返回3家高风险供应商", "high", 3),
        ("找出15个低风险供应商", "low", 15),
        ("最多展示20家中风险供应商", "medium", 20),
        ("List 6 high-risk suppliers", "high", 6),
        ("我想看12家低风险的供应商", "low", 12),
        ("筛选4个中风险供应商", "medium", 4),
    ]
    for query, risk_level, limit in supplier_filters:
        add(
            "supplier_filter",
            query,
            "TOOL_CALL",
            "list_suppliers",
            {"risk_level": risk_level, "limit": limit},
        )

    order_queries = [
        ("查询采购订单 PO-2026-000001", "PO-2026-000001"),
        ("查看订单 PO-2026-000268 的详情", "PO-2026-000268"),
        ("PO-2026-000545 的金额和状态是什么？", "PO-2026-000545"),
        ("帮我调取 PO-2026-001976", "PO-2026-001976"),
        ("检索采购单 PO-2026-002134", "PO-2026-002134"),
        ("订单 PO-2026-002148 预计什么时候交付？", "PO-2026-002148"),
        ("Show purchase order PO-2026-002991", "PO-2026-002991"),
        ("查询不存在的订单 PO-2026-999999", "PO-2026-999999"),
    ]
    for query, order_number in order_queries:
        add(
            "order_lookup",
            query,
            "TOOL_CALL",
            "get_purchase_order",
            {"order_number": order_number},
        )

    risk_events = [
        ("查询最近20条高风险事件", {"severity": "high", "limit": 20}),
        ("列出10条付款失败风险事件", {"event_type": "payment_failure", "limit": 10}),
        ("返回5条严重级别为 critical 的事件", {"severity": "critical", "limit": 5}),
        ("查询8条交付延期事件", {"event_type": "delivery_delay", "limit": 8}),
        ("给我12条中风险事件", {"severity": "medium", "limit": 12}),
        ("查看3条低风险事件", {"severity": "low", "limit": 3}),
        ("列出7条高风险付款失败事件", {"severity": "high", "event_type": "payment_failure", "limit": 7}),
        ("查询9条 critical 交付延期事件", {"severity": "critical", "event_type": "delivery_delay", "limit": 9}),
        ("Show 6 high-severity risk events", {"severity": "high", "limit": 6}),
        ("调取最近15条风险事件", {"limit": 15}),
    ]
    for query, arguments in risk_events:
        add("risk_event", query, "TOOL_CALL", "list_risk_events", arguments)

    high_risk_searches = [
        ("查询最近365天金额超过10万元、延期至少7天、历史延期至少2次的订单，最多5条", 365, 100000, 7, 2, 5),
        ("查近180天金额20万元以上、延期10天、历史延期3次的高风险订单，返回10条", 180, 200000, 10, 3, 10),
        ("筛选近90天金额5万元以上且延期5天的订单，最多8条", 90, 50000, 5, 2, 8),
        ("查询近30天金额超过30万元、延期15天、历史延期4次的订单，返回6条", 30, 300000, 15, 4, 6),
        ("找出近730天金额50万元以上、延期7天且历史延期2次的订单，最多12条", 730, 500000, 7, 2, 12),
        ("Search 5 risky orders from the last 120 days over CNY 150000, delayed 9 days, with 2 prior delays", 120, 150000, 9, 2, 5),
        ("查近60天金额8万元以上、延期3天、历史延期1次的订单，最多4条", 60, 80000, 3, 1, 4),
        ("返回近3650天金额100万元以上、延期20天、历史延期5次的订单，最多20条", 3650, 1000000, 20, 5, 20),
        ("查询最近270天金额12万元以上、延期8天、历史延期2次的订单，返回7条", 270, 120000, 8, 2, 7),
    ]
    for query, days, amount, delay, history, limit in high_risk_searches:
        add(
            "risk_order_search",
            query,
            "TOOL_CALL",
            "find_high_risk_orders",
            {
                "days": days,
                "min_amount": amount,
                "min_delay_days": delay,
                "min_historical_delays": history,
                "limit": limit,
            },
        )

    write_queries = [
        (1, "Investigate delivery risk", "Manual investigation is required", "high"),
        (2, "Review payment failure", "Finance team should review this payment failure", "critical"),
        (3, "Check supplier incident", "Procurement should contact the supplier", "medium"),
        (4, "Monitor delivery delay", "Track the delayed delivery and report progress", "low"),
        (5, "Escalate operational risk", "Manager review is required for this incident", "high"),
        (6, "Investigate critical event", "Start a critical risk investigation immediately", "critical"),
    ]
    for event_id, title, description, priority in write_queries:
        add(
            "write_operation",
            f"为风险事件{event_id}创建工单，标题为{title}，描述为{description}，优先级为{priority}",
            "TOOL_CALL",
            "create_risk_ticket",
            {
                "risk_event_id": event_id,
                "title": title,
                "description": description,
                "priority": priority,
            },
            "BLOCKED",
        )

    assert len(cases) == 60
    return cases


def workflow_cases() -> list[dict[str, Any]]:
    raw_cases = [
        ("general", "什么是供应链风险？", "DIRECT_RESPONSE", [], None),
        ("general", "供应商风险管理的目的是什么？", "DIRECT_RESPONSE", [], None),
        ("general", "采购订单和采购合同有什么区别？", "DIRECT_RESPONSE", [], None),
        ("general", "为什么高风险操作需要人工审批？", "DIRECT_RESPONSE", [], None),
        ("supplier", "查询供应商 SUP-2026-0003 的详细信息", "TOOL_CALL", ["get_supplier"], None),
        ("supplier", "列出5个高风险供应商", "TOOL_CALL", ["list_suppliers"], None),
        ("supplier", "查看 SUP-2026-0031 的评级和风险等级", "TOOL_CALL", ["get_supplier"], None),
        ("supplier", "返回10家低风险供应商", "TOOL_CALL", ["list_suppliers"], None),
        ("order", "查询采购订单 PO-2026-000268", "TOOL_CALL", ["get_purchase_order"], None),
        ("order", "分析近365天金额超过10万元、延期7天且历史延期2次的订单", "TOOL_CALL", ["find_high_risk_orders"], None),
        ("risk", "查询10条付款失败风险事件", "TOOL_CALL", ["list_risk_events"], None),
        ("risk", "列出最近8条高风险事件", "TOOL_CALL", ["list_risk_events"], None),
        ("policy_rag", "根据企业政策，延期多少天属于重大交付延期？", "TOOL_CALL", ["search_enterprise_policy"], None),
        ("policy_rag", "公司政策如何定义高价值采购？", "TOOL_CALL", ["search_enterprise_policy"], None),
        ("policy_rag", "按照内部制度，哪些采购需要经理审核？", "TOOL_CALL", ["search_enterprise_policy"], None),
        ("policy_rag", "企业政策对 AI 创建风险工单有什么限制？", "TOOL_CALL", ["search_enterprise_policy"], None),
        ("policy_rag", "供应商出现几次严重延期后应提高风险等级？", "TOOL_CALL", ["search_enterprise_policy"], None),
        ("multi_step", "分析近365天金额超过10万元、延期至少7天且历史延期2次的订单，并按企业政策判断是否升级", "TOOL_CALL", ["find_high_risk_orders", "search_enterprise_policy"], None),
        ("multi_step", "查询供应商 SUP-2026-0003，并结合企业政策说明应该如何监控", "TOOL_CALL", ["get_supplier", "search_enterprise_policy"], None),
        ("multi_step", "查看订单 PO-2026-000268，并根据采购制度判断是否需要额外风险审查", "TOOL_CALL", ["get_purchase_order", "search_enterprise_policy"], None),
        ("multi_step", "查询最近高风险事件，并结合风险升级政策给出处置建议", "TOOL_CALL", ["list_risk_events", "search_enterprise_policy"], None),
        ("multi_step", "列出高风险供应商，并根据供应商政策说明人工复核标准", "TOOL_CALL", ["list_suppliers", "search_enterprise_policy"], None),
        ("multi_step", "查询10条付款失败事件，并结合企业风险政策判断是否需要升级", "TOOL_CALL", ["list_risk_events", "search_enterprise_policy"], None),
        ("multi_step", "分析近180天20万元以上且延期10天的订单，并引用政策给出结论", "TOOL_CALL", ["find_high_risk_orders", "search_enterprise_policy"], None),
        ("rbac", "为风险事件1创建高优先级调查工单", "TOOL_CALL", ["create_risk_ticket"], "PERMISSION_DENIED"),
        ("rbac", "为风险事件2创建严重级别调查工单", "TOOL_CALL", ["create_risk_ticket"], "PERMISSION_DENIED"),
        ("rbac", "为风险事件3创建中优先级风险工单", "TOOL_CALL", ["create_risk_ticket"], "PERMISSION_DENIED"),
        ("approval", "为风险事件1创建高优先级调查工单", "TOOL_CALL", ["create_risk_ticket"], "APPROVAL_REQUIRED"),
        ("approval", "为风险事件2创建严重优先级调查工单", "TOOL_CALL", ["create_risk_ticket"], "APPROVAL_REQUIRED"),
        ("approval", "为风险事件3创建中优先级调查工单", "TOOL_CALL", ["create_risk_ticket"], "APPROVAL_REQUIRED"),
    ]

    cases = []
    for index, (category, query, route, tools, security) in enumerate(raw_cases, start=1):
        role = "manager" if category == "approval" else "employee"
        case = {
            "id": f"EW{index:03d}",
            "source": "synthetic",
            "category": category,
            "input": query,
            "role": role,
            "expected_route": route,
            "expected_tools": tools,
        }
        if security is not None:
            case["expected_security_status"] = security
        cases.append(case)

    assert len(cases) == 30
    return cases


def rag_cases() -> list[dict[str, Any]]:
    rows = [
        ("高价值采购的金额标准是多少？", "procurement_policy.txt"),
        ("订单金额超过多少人民币属于高价值采购？", "procurement_policy.txt"),
        ("超过五十万元的采购需要谁审核？", "procurement_policy.txt"),
        ("高价值订单延期后是否需要额外风险审查？", "procurement_policy.txt"),
        ("修改采购记录需要什么授权？", "procurement_policy.txt"),
        ("重复出现交付问题的供应商应该怎么处理？", "procurement_policy.txt"),
        ("采购经理审核的金额门槛是什么？", "procurement_policy.txt"),
        ("几天以上的交付延期属于重大延期？", "supplier_policy.txt"),
        ("十五天以上的延期应该如何定级？", "supplier_policy.txt"),
        ("供应商半年内多次延期应如何升级？", "supplier_policy.txt"),
        ("评估供应商风险应参考哪些数据？", "supplier_policy.txt"),
        ("供应商出现多少次严重延期属于风险升高？", "supplier_policy.txt"),
        ("重复重大延期是否需要人工采购复核？", "supplier_policy.txt"),
        ("供应商风险评估是否应该考虑付款事件？", "supplier_policy.txt"),
        ("AI 能否未经批准直接创建调查工单？", "risk_policy.txt"),
        ("高严重度运营风险由谁复核？", "risk_policy.txt"),
        ("创建调查工单属于读操作还是写操作？", "risk_policy.txt"),
        ("风险证据不足时系统应该怎么回答？", "risk_policy.txt"),
        ("风险分析中事实与推断应该如何处理？", "risk_policy.txt"),
        ("哪些状态变更操作必须人工审批？", "risk_policy.txt"),
    ]
    return [
        {
            "id": f"ER{index:03d}",
            "source": "synthetic",
            "query": query,
            "expected_sources": [expected_source],
        }
        for index, (query, expected_source) in enumerate(rows, start=1)
    ]


def main() -> None:
    common_cases = baseline_cases()

    for case in common_cases:
        case["expected_route"] = case["expected_routing"]
        case["expected_tools"] = (
            [case["expected_tool"]]
            if case["expected_tool"]
            else []
        )
        case["role"] = (
            "manager"
            if case["category"] == "write_operation"
            else "employee"
        )
        if case["category"] == "write_operation":
            case["expected_security_status"] = "APPROVAL_REQUIRED"

    dataset = {
        "metadata": {
            "name": "EnterpriseOps Agent Unified Synthetic Benchmark",
            "version": "1.0",
            "source": "synthetic",
            "unique_case_count": 110,
            "common_case_count": 60,
            "workflow_extension_case_count": 30,
            "rag_case_count": 20,
        },
        "common_agent_cases": common_cases,
        "workflow_extension_cases": workflow_cases(),
        "rag_cases": rag_cases(),
    }
    write_dataset(dataset)


if __name__ == "__main__":
    main()
