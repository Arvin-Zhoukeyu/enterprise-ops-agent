from app.tools import (
    load_tools,
    tool_registry,
)


def main():

    load_tools()

    print(
        "\nRegistered tools:"
    )

    for tool in (
        tool_registry.list_tools()
    ):

        print(
            f"- {tool.name}"
            f" | permission="
            f"{tool.permission}"
            f" | side_effect="
            f"{tool.side_effect}"
        )


if __name__ == "__main__":
    main()