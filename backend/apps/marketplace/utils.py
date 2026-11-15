import re


_PHONE_PATTERN = re.compile(r"^(?:\+?98|0)?9\d{9}$")


def format_user_display_name(
    user,
    fallback: str = "کاربر تفاخر",
    *,
    first_name_only: bool = False,
) -> str:
    """
    Returns a public display name for a User without ever falling back to raw phone numbers.
    """
    if not user:
        return fallback

    first_name = (getattr(user, "first_name", "") or "").strip()
    last_name = (getattr(user, "last_name", "") or "").strip()
    full_name = f"{first_name} {last_name}".strip()

    if not full_name:
        return fallback

    candidate = full_name.split()[0] if first_name_only else full_name
    if not candidate or _PHONE_PATTERN.fullmatch(candidate):
        return fallback

    return candidate

