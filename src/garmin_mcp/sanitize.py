"""Strip personally identifiable information from Garmin API responses."""

from typing import Any

PII_KEYS = frozenset({
    "ownerId",
    "ownerFullName",
    "ownerDisplayName",
    "ownerProfileImageUrlLarge",
    "ownerProfileImageUrlMedium",
    "ownerProfileImageUrlSmall",
    "userId",
    "userProfilePK",
    "userProfilePk",
    "userProfileId",
    "profileId",
    "profileNumber",
    "userPro",
    "userRoles",
    "displayName",
    "fullName",
    "profileImgNameLarge",
    "profileImgNameMedium",
    "profileImgNameSmall",
    "startLatitude",
    "startLongitude",
    "endLatitude",
    "endLongitude",
})


def strip_pii(data: Any) -> Any:
    """Recursively remove PII keys from dicts/lists."""
    if isinstance(data, dict):
        return {k: strip_pii(v) for k, v in data.items() if k not in PII_KEYS}
    if isinstance(data, list):
        return [strip_pii(item) for item in data]
    return data
