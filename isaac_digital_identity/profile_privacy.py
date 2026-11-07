"""Explicit projections: public data, collaboration candidates, private rules.

Collaboration candidates are not grants and are never exported publicly.
Unknown fields are excluded, including unknown nested project/skill fields.
"""
from copy import deepcopy

PUBLIC_FIELDS = (
    "id", "name", "short_name", "initials", "role", "subtitle", "location",
    "email", "about", "manifesto", "education", "experience", "certifications",
    "projects", "skills", "languages", "photo",
)
NESTED_FIELDS = {
    "education": ("school", "degree", "dates", "detail"),
    "experience": ("company", "position", "dates", "desc"),
    "certifications": ("name", "issuer", "dates"),
    "projects": ("id", "number", "title", "category", "tags", "year", "description", "detail", "outcome", "visual"),
    "skills": ("name", "items"),
}
COLLABORATION_FIELDS = ("id", "name", "role", "objective", "interests", "skills", "projects")


def project_fields(profile, fields):
    result = {}
    for key in fields:
        value = profile.get(key)
        if key in NESTED_FIELDS and isinstance(value, list):
            items = []
            for item in value[:30]:
                if not isinstance(item, dict):
                    continue
                safe = {}
                for field in NESTED_FIELDS[key]:
                    val = item.get(field)
                    if isinstance(val, str):
                        safe[field] = val
                    elif field in ("items", "tags") and isinstance(val, list):
                        safe[field] = [x for x in val[:30] if isinstance(x, str)]
                items.append(safe)
            result[key] = items
        elif key == "interests" and isinstance(value, list):
            result[key] = [x for x in value[:20] if isinstance(x, str)]
        elif isinstance(value, str):
            result[key] = value
    return result


def public_profile(profile):
    privacy = profile.get("privacy", {})
    requested = privacy.get("public_fields", PUBLIC_FIELDS) if isinstance(privacy, dict) else PUBLIC_FIELDS
    if not isinstance(requested, (list, tuple)):
        requested = ()
    # Public identity is required; all other existing public fields can be hidden.
    fields = {"id", "name", "role"} | (set(x for x in requested if isinstance(x, str)) & set(PUBLIC_FIELDS))
    return project_fields(profile, fields)


def collaboration_profile(profile):
    return project_fields(profile, COLLABORATION_FIELDS)


def private_agent_config(profile):
    rules = profile.get("constraints", {})
    if not isinstance(rules, dict):
        return {}
    result = {k: rules[k] for k in ("collaboration_mode", "preferred_scope") if isinstance(rules.get(k), str)}
    hours = rules.get("max_hours_week")
    if isinstance(hours, int) and not isinstance(hours, bool) and 1 <= hours <= 168:
        result["max_hours_week"] = hours
    prohibited = rules.get("prohibited")
    if isinstance(prohibited, list):
        result["prohibited"] = [x for x in prohibited if isinstance(x, str)]
    return deepcopy(result)
