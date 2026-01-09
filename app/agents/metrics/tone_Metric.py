class ToneOutputValidator:
    def validate(self, result: dict) -> dict:
        issues = result.get("issues", [])

        return {
            "has_issues": bool(issues),
            "issue_count": len(issues),
            "schema_valid": isinstance(issues, list),
        }
