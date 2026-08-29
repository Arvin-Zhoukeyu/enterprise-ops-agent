from app.tools import (
    load_tools,
    tool_registry,
)


def main():

    load_tools()

    print(
        "\n=== Test get_supplier ==="
    )

    result = tool_registry.execute(
        "get_supplier",
        {
            "supplier_code":
                "SUP-2026-0003"
        },
    )

    print(result)

    print(
        "\n=== Test high-risk orders ==="
    )

    result = tool_registry.execute(
        "find_high_risk_orders",
        {
            "days": 365,
            "min_amount": 100000,
            "min_delay_days": 7,
            "min_historical_delays": 2,
            "limit": 5,
        },
    )

    print(result)


if __name__ == "__main__":
    main()