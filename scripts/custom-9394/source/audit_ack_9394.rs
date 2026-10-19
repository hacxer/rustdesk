// Compatibility is limited to the exact legacy 9394 audit acknowledgment.
// This function never authorizes a connection or suppresses a failed audit.
pub fn is_legacy_success(text: &str) -> bool {
    let Ok(value) = serde_json::from_str::<serde_json::Value>(text) else {
        return false;
    };
    let Some(object) = value.as_object() else {
        return false;
    };
    object.len() == 3
        && object.get("code").and_then(|v| v.as_i64()) == Some(0)
        && object.get("message").and_then(|v| v.as_str()) == Some("success")
        && object.get("data").and_then(|v| v.as_str()) == Some("")
}

#[cfg(test)]
mod tests {
    use super::is_legacy_success;

    #[test]
    fn accepts_only_documented_success_envelope() {
        assert!(is_legacy_success(r#"{"code":0,"message":"success","data":""}"#));
        assert!(is_legacy_success(r#" { "data":"", "message":"success", "code":0 } "#));
    }

    #[test]
    fn rejects_failure_and_ambiguous_responses() {
        for text in [
            "", "not json", "<html>maintenance</html>", "null", "[]",
            r#"{"code":1,"message":"success","data":""}"#,
            r#"{"code":"0","message":"success","data":""}"#,
            r#"{"code":0.0,"message":"success","data":""}"#,
            r#"{"code":0,"message":"failed","data":""}"#,
            r#"{"code":0,"message":"success","data":null}"#,
            r#"{"code":0,"message":"success","data":"unrecognized"}"#,
            r#"{"code":0,"message":"success","data":"","error":"db failure"}"#,
            r#"{"error":"database unavailable"}"#,
            r#"{"code":0,"message":"success"}"#,
        ] {
            assert!(!is_legacy_success(text), "incorrect success: {text}");
        }
    }
}
