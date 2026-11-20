import re
RULES=[
(r"\\b(password|passcode|otp|verification code|recovery key)\\b","Message mentions authentication secrets. Never request or share passwords or codes."),
(r"\\b(payment|wire transfer|crypto|gift card|bank transfer)\\b","Payment language detected; review possible financial-scam context."),
(r"\\b(guaranteed recovery|100% recover|guaranteed unlock)\\b","Unrealistic guarantee language detected; review expectations."),
(r"https?://","External link present; inspect safely before opening.")
]
def assess_risk(message,evidence=""):
    flags=[advice for pattern,advice in RULES if re.search(pattern,(message+" "+evidence),re.I)]
    if len(message.strip())<80: flags.append("Short description; request more context during manual review.")
    return {"score":min(100,len(flags)*18),"flags":flags}
