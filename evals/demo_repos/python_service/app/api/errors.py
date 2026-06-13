def validation_error_handler(errors: list[dict[str, str]]) -> dict[str, object]:
    """Convert validation errors to a stable API response."""
    fields = [
        {"field": error.get("field", "unknown"), "message": error.get("message", "invalid value")}
        for error in errors
    ]
    return {"status": 422, "error": "validation_failed", "fields": fields}
