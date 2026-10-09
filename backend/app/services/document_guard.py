"""Document Guard — deterministic heuristic scanner for documents an agent will read.

Findings are *risk signals*, not a malware verdict. Nothing here authorizes or
blocks an action; enforcement happens only in the gateway. The raw document is
never persisted or logged — only short, redacted evidence is returned.
"""

from __future__ import annotations
import hashlib
import re
from dataclasses import dataclass, asdict

MAX_DOCUMENT_CHARS = 100_000
SEVERITY_ORDER = {"review": 1, "elevated": 2, "high": 3}
RISK_LABELS = {0: "no_signals", 1: "review", 2: "elevated", 3: "high"}

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)+\b")
URL_RE = re.compile(r"\bhttps?://[^\s<>\"')]+", re.IGNORECASE)
CARD_RE = re.compile(r"\b(?:\d[ \-]?){12,18}\d\b")
PHONE_RE = re.compile(r"(?<![\w])\+?\d{1,3}[\s\-.]?\(?\d{2,4}\)?[\s\-.]?\d{3,4}[\s\-.]?\d{3,4}(?![\w])")
ZERO_WIDTH_RE = re.compile("[\u200b\u200c\u200d\u2060\ufeff]")
CREDENTIAL_RE = re.compile(r"\b(password|passwd|api[_\- ]?key|secret|access[_\- ]?token)\s*[:=]\s*\S+", re.IGNORECASE)

INJECTION_PATTERNS: list[tuple[str, str]] = [
    (r"\b(ignore|disregard|forget|override)\b[^.\n]{0,40}\b(previous|prior|above|earlier|all|system)\b[^.\n]{0,20}\b(instructions?|rules|prompts?|guidelines)\b",
     "Tells the reader to discard its existing instructions — a classic prompt-injection pattern."),
    (r"\byou are now\b|\bact as (an? )?(unrestricted|admin|developer|jailbroken)\b|\bdeveloper mode\b|\bjailbreak\b",
     "Attempts to redefine the AI's role or unlock restricted behaviour."),
    (r"\b(system prompt|hidden instructions?)\b",
     "Refers to the AI's system prompt or hidden instructions."),
    (r"\b(do not|don't|never) (tell|inform|notify|alert) (the )?(user|human|owner|reviewer)\b",
     "Asks the AI to hide its actions from the person it works for."),
    (r"\b(ai|assistant|agent|llm|model)s?\b[^.\n]{0,40}\b(must|should|need to|please)\b[^.\n]{0,40}\b(forward|send|email|upload|share|transfer|delete)\b",
     "Embedded instruction addressed to an AI agent asking it to take an action."),
]

SHARING_RE = re.compile(
    r"\b(forward|send|email|e-mail|upload|share|transmit|post|transfer|exfiltrate)\b[^.]{0,80}?\b(to|with)\b",
    re.IGNORECASE,
)
URL_SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "ow.ly", "rb.gy"}


@dataclass
class Finding:
    type: str
    severity: str
    evidence: str
    explanation: str


def redact_email(value: str) -> str:
    local, _, domain = value.partition("@")
    return f"{local[:2]}***@{domain}"


def _luhn_ok(digits: str) -> bool:
    total, parity = 0, len(digits) % 2
    for i, ch in enumerate(digits):
        d = int(ch)
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def _snippet(text: str, start: int, end: int, limit: int = 90) -> str:
    raw = " ".join(text[start:end].split())
    raw = EMAIL_RE.sub(lambda m: redact_email(m.group(0)), raw)
    return raw if len(raw) <= limit else raw[: limit - 1] + "…"


def scan_text(text: str) -> dict:
    findings: list[Finding] = []
    seen: set[tuple[str, str]] = set()

    def add(f: Finding) -> None:
        key = (f.type, f.evidence)
        if key not in seen and len(findings) < 50:
            seen.add(key)
            findings.append(f)

    for pattern, explanation in INJECTION_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            add(Finding("prompt_injection", "high", _snippet(text, m.start(), m.end()), explanation))

    if ZERO_WIDTH_RE.search(text):
        add(Finding("hidden_text", "elevated", f"{len(ZERO_WIDTH_RE.findall(text))} zero-width character(s)",
                    "Invisible characters can hide instructions from a human reviewer."))

    for m in SHARING_RE.finditer(text):
        add(Finding("external_sharing_request", "elevated", _snippet(text, m.start(), min(len(text), m.end() + 40)),
                    "Language asking for data to be sent or shared somewhere."))

    for m in EMAIL_RE.finditer(text):
        add(Finding("email_address", "review", redact_email(m.group(0)),
                    "An email address the document might steer an agent towards. Check it is expected."))

    for m in URL_RE.finditer(text):
        url = m.group(0)
        host = re.sub(r"^https?://", "", url, flags=re.IGNORECASE).split("/")[0].split(":")[0].lower()
        shown = f"{url[:8]}{host}/…" if len(url) > len(host) + 9 else url
        if re.fullmatch(r"[\d.]+", host):
            add(Finding("risky_url", "elevated", shown, "Link points to a raw IP address instead of a named host."))
        elif host in URL_SHORTENERS:
            add(Finding("risky_url", "elevated", shown, "Shortened link hides its real destination."))
        elif url.lower().startswith("http://"):
            add(Finding("risky_url", "review", shown, "Unencrypted (http) link."))
        else:
            add(Finding("url", "review", shown, "External link — verify before an agent follows it."))

    card_spans: list[tuple[int, int]] = []
    for m in CARD_RE.finditer(text):
        digits = re.sub(r"\D", "", m.group(0))
        if 13 <= len(digits) <= 19 and _luhn_ok(digits):
            card_spans.append(m.span())
            add(Finding("payment_card_number", "elevated", f"**** **** **** {digits[-4:]}",
                        "Looks like a payment card number (passes the Luhn check)."))

    for m in PHONE_RE.finditer(text):
        digits = re.sub(r"\D", "", m.group(0))
        overlaps_card = any(m.start() < end and start < m.end() for start, end in card_spans)
        if 9 <= len(digits) <= 15 and not overlaps_card:
            add(Finding("phone_number", "review", f"***{digits[-2:]}", "Phone number — personal contact data."))

    for m in CREDENTIAL_RE.finditer(text):
        add(Finding("credential", "high", f"{m.group(1)}: [REDACTED]", "Text appears to contain a credential or secret."))

    level = max((SEVERITY_ORDER[f.severity] for f in findings), default=0)
    findings.sort(key=lambda f: -SEVERITY_ORDER[f.severity])
    return {
        "risk_level": RISK_LABELS[level],
        "findings": [asdict(f) for f in findings],
        "stats": {
            "characters": len(text),
            "lines": text.count("\n") + 1 if text else 0,
            "sha256_prefix": hashlib.sha256(text.encode()).hexdigest()[:12],
        },
    }


def extract_agent_proposal(text: str) -> dict:
    """Deterministic DEMO agent: a naive assistant that obeys instructions found in the document.

    If the document asks to send/forward data to an email address, the agent proposes
    send_external_email to that address; otherwise it proposes a local summary.
    This simulates a compromised agent — the gateway, not this function, decides.
    """
    for m in SHARING_RE.finditer(text):
        window = text[m.start(): m.end() + 120]
        email = EMAIL_RE.search(window)
        if email:
            return {
                "tool_name": "send_external_email",
                "arguments": {
                    "to": email.group(0),
                    "subject": "Invoice invoice-42",
                    "body": "Forwarding invoice-42 as requested in the document.",
                    "attachment": "invoice-42",
                },
                "rationale": "The document instructed the agent to send the invoice to an external address.",
            }
    return {
        "tool_name": "generate_local_summary",
        "arguments": {"invoice_id": "invoice-42"},
        "rationale": "No sharing instruction found; the agent writes a local summary as its task requires.",
    }
