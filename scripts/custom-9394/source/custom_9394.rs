use hbb_common::{
    config::{Config, LocalConfig, DEFAULT_LOCAL_SETTINGS, DEFAULT_SETTINGS},
    log,
};
use std::{collections::HashMap, sync::Once};

static INITIALIZE: Once = Once::new();
const PROFILE_MARKER: &str = "9394-profile-v2";
const PASSWORD_MARKER: &str = "9394-password-initialized-v1";
const SERVER_KEYS: [&str; 4] = ["custom-rendezvous-server", "relay-server", "api-server", "key"];
const LOCAL_KEYS: [&str; 4] = [
    "enable-tcp-punch", "enable-ipv6-punch", "enable-check-update", "show-scam-warning",
];

pub fn initialize() {
    INITIALIZE.call_once(|| {
        let defaults: HashMap<String, String> = match serde_json::from_str(
            include_str!("../config/custom-9394.json"),
        ) {
            Ok(value) => value,
            Err(error) => {
                log::error!("Invalid 9394 defaults: {error}");
                return;
            }
        };
        let migrate = LocalConfig::get_option(PROFILE_MARKER) != "Y";
        // Read existing values before installing defaults. Preserve nonempty overrides.
        if migrate {
            for key in SERVER_KEYS {
                if Config::get_option(key).trim().is_empty() {
                    if let Some(value) = defaults.get(key) {
                        Config::set_option(key.to_owned(), value.to_owned());
                    }
                }
            }
        }
        for (key, value) in defaults {
            if LOCAL_KEYS.contains(&key.as_str()) {
                DEFAULT_LOCAL_SETTINGS.write().unwrap().insert(key, value);
            } else {
                DEFAULT_SETTINGS.write().unwrap().insert(key, value);
            }
        }
        if migrate {
            Config::set_option("allow-websocket".into(), "N".into());
            // One migration only; later explicit user choices remain editable.
            LocalConfig::set_option("enable-check-update".into(), "N".into());
            LocalConfig::set_option("show-scam-warning".into(), "N".into());
            LocalConfig::set_option(PROFILE_MARKER.into(), "Y".into());
        }
        if LocalConfig::get_option(PASSWORD_MARKER) != "Y" {
            let initialized = if Config::has_permanent_password() {
                true
            } else {
                match option_env!("RUSTDESK_PRESET_PASSWORD") {
                    Some(password) if !password.is_empty() => Config::set_permanent_password(password),
                    _ => false,
                }
            };
            if initialized {
                LocalConfig::set_option(PASSWORD_MARKER.to_owned(), "Y".to_owned());
            } else {
                log::error!("9394 permanent password initialization failed");
            }
        }
    });
}
