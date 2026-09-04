ROLE_PERMISSIONS = {

    "employee": {
        "READ",
    },

    "manager": {
        "READ",
        "WRITE",
    },

    "admin": {
        "READ",
        "WRITE",
        "ADMIN",
    },
}


def has_permission(
    role: str,
    required_permission: str,
) -> bool:

    permissions = (
        ROLE_PERMISSIONS.get(
            role,
            set(),
        )
    )

    return (
        required_permission
        in permissions
    )