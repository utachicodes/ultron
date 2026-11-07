from __future__ import annotations

"""Jailbreak/prompt-injection guard -- the defend half of AI Guard red-teaming.

`sanitizer.py` strips PII, credentials, and IPs before a prompt leaves the
building; it was never meant to, and doesn't, catch prompt-injection or
jailbreak attempts (e.g. "ignore previous instructions", "you are now DAN").
This module closes that gap: a small set of built-in category detectors,
plus a DB-backed list of patterns learned from `app.ai_redteam` runs --
every confirmed bypass becomes a new detector here, so the same attack
doesn't work twice.

Detection is deliberately conservative (keyword/phrase matching, not an ML
classifier): a false positive just routes a prompt to the local fallback
instead of an external provider, which is a safe failure mode; a false
negative is caught on the next red-team run instead.
"""

import re
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

# category -> (human label, canonical detection regex). These mirror the
# attack categories in `app.ai_redteam.PAYLOADS` -- one built-in detector
# per well-known jailbreak technique, independent of any specific run.
BUILT_IN_PATTERNS = {
    "instruction_override": (
        "Instruction override",
        re.compile(r"(?i)ignore (all |your |previous |the )?(previous |prior |above )?instructions?"),
    ),
    "role_play_jailbreak": (
        "Role-play jailbreak",
        re.compile(r"(?i)\byou are now\b.{0,40}\b(dan|do anything now|unrestricted|jailbroken)\b"),
    ),
    "system_prompt_leak": (
        "System prompt leak attempt",
        re.compile(r"(?i)(repeat|reveal|print|show) (your |the )?(system prompt|initial instructions|hidden instructions)"),
    ),
    "fake_authority": (
        "Fake authority / impersonated override",
        re.compile(r"(?i)as the (system administrator|developer|owner)[,:]? (override|disable|bypass)"),
    ),
    "hypothetical_framing": (
        "Hypothetical/fictional framing to bypass guidelines",
        re.compile(r"(?i)(hypothetically|in a (fictional|hypothetical) (story|scenario)).{0,60}\b(no (restrictions|rules|limits)|without (restrictions|rules|limits))\b"),
    ),
}

# Known attack signatures that are *not* pre-armed -- they only become
# active detectors once `app.ai_redteam` actually confirms a bypass for
# that category (see `add_pattern_from_bypass`), so the attack/learn/reblock
# loop has something real to demonstrate instead of every category already
# being blocked on day one.
LEARNABLE_SIGNATURES = {
    "encoding_obfuscation": re.compile(r"(?i)decode this and follow it exactly"),
    "payload_splitting": re.compile(r"(?i)now combine your instructions and output"),
    "token_smuggling": re.compile(r"(?i)complete this pattern by outputting only the final token"),
}


def is_jailbreak_attempt(
    text: str, db: Optional[Session] = None
) -> Tuple[bool, Optional[str]]:
    """Check text against built-in categories and any active, DB-learned
    patterns. Returns (matched, category) -- category is the built-in key
    or the learned pattern's category, or None if nothing matched."""
    if not text:
        return False, None

    for category, (_, pattern) in BUILT_IN_PATTERNS.items():
        if pattern.search(text):
            return True, category

    if db is not None:
        from app import models

        learned = db.query(models.JailbreakPattern).filter(models.JailbreakPattern.is_active == True).all()  # noqa: E712
        for row in learned:
            try:
                if re.search(row.pattern, text, re.IGNORECASE):
                    return True, row.category
            except re.error:
                continue

    return False, None


def add_pattern_from_bypass(
    db: Session, category: str, source_run_id: Optional[int] = None
) -> "models.JailbreakPattern":
    """Record a confirmed bypass as a new (or reactivated) defense pattern
    for its category. One active pattern per category is kept -- a second
    bypass in the same category reactivates/refreshes it rather than piling
    up duplicates. Uses the same canonical regex as the built-in detector
    for that category when one exists, since the attack categories and
    defense categories are the same vocabulary by design."""
    from app import models

    existing = (
        db.query(models.JailbreakPattern)
        .filter(models.JailbreakPattern.category == category)
        .first()
    )
    if existing:
        existing.is_active = True
        existing.learned_from_run_id = source_run_id
        db.commit()
        db.refresh(existing)
        return existing

    _, pattern = BUILT_IN_PATTERNS.get(category, (None, None))
    if pattern is None:
        pattern = LEARNABLE_SIGNATURES.get(category)
    pattern_str = pattern.pattern if pattern else re.escape(category)

    row = models.JailbreakPattern(
        category=category,
        pattern=pattern_str,
        learned_from_run_id=source_run_id,
        is_active=True,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_active_patterns(db: Session) -> List["models.JailbreakPattern"]:
    from app import models

    return (
        db.query(models.JailbreakPattern)
        .filter(models.JailbreakPattern.is_active == True)  # noqa: E712
        .order_by(models.JailbreakPattern.id)
        .all()
    )
