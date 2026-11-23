import json
from pathlib import Path
r = json.loads(Path("logs/fp_register_20261031_225335.json").read_text(encoding="utf-8"))
# redact
safe = {k: v for k,v in r.items()}
print("result keys ok:", sorted(safe.keys()))
print("registration_ok:", safe["registration_ok"])
print("registration_attempted:", safe["registration_attempted"])
print("exit_not_home:", safe["exit_not_home"])
print("fp_registered:", safe["fp_registered"])
print("model:", safe["model"])
print("time_zone:", safe["time_zone"])
print("country:", safe["country"])
print("profile:", safe["profile"])
print("log:", safe["log"])
print("http_status_deviceprofile:", safe["http_status_deviceprofile"])
d = json.loads(Path("mitm") / safe["profile"]).read_text(encoding="utf-8") if False else json.loads((Path("mitm")/safe["profile"]).read_text(encoding="utf-8"))
print("profile model:", d.get("model"), "tz:", d.get("time_zone"), "fp_reg:", d.get("fp_registered"))
print("has user_agent:", bool(d.get("user_agent")), "has fpx:", bool(d.get("fpx_user_agent")))
# ensure no accidental POST by checking we never imported/called deviceprofile in log
log = Path("logs")/safe["log"]
t = log.read_text(encoding="utf-8")
print("log mentions POST:", "POST" in t)
print("log mentions СТОП:", "СТОП" in t)
