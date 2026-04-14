"""
Suspension Tracker

Anki add-on that records the date a card is suspended or unsuspended and 
makes those dates searchable via tags and custom browser columns.

Requires Anki 2.1.45+
"""

from __future__ import annotations

import re
import datetime
from aqt import mw, gui_hooks
from aqt.qt import *
from .gui import DateRangeDialog

try:
    from anki.collection import BrowserColumns
    HAS_BROWSER_COLUMNS = True
except ImportError:
    HAS_BROWSER_COLUMNS = False

# Tags used for tracking
NS = "suspension-tracker"
TAG_UNSUSPEND = f"{NS}::unsuspended"
TAG_SUSPEND = f"{NS}::suspended"

EVENT_MAP = {
    "unsuspended": TAG_UNSUSPEND,
    "suspended": TAG_SUSPEND,
}

_DATE_REGEX = r'(?:\d{4}-\d{2}-\d{2}|\*)'
TOKEN_RE = re.compile(
    rf'\b(?:tag:{NS}::(?:unsuspended|suspended)::[\d\-*]+|tracker:(?:unsuspended|suspended):({_DATE_REGEX}):({_DATE_REGEX}))\b',
    re.IGNORECASE,
)

# State for tracking changes
_suspended_snapshot: set[int] = set()
_snapshot_loaded = False

def _set_event_tag(note, prefix: str, date_str: str) -> None:
    note.tags = [t for t in note.tags if not t.startswith(f"{prefix}::")]
    note.tags.append(f"{prefix}::{date_str}")

def _get_event_date(note, prefix: str) -> str:
    target = f"{prefix}::"
    for tag in note.tags:
        if tag.startswith(target):
            return tag[len(target):]
    return ""

def _stamp_notes(card_ids: list[int], prefix: str, date_str: str) -> None:
    seen_notes: set[int] = set()
    for cid in card_ids:
        try:
            card = mw.col.get_card(cid)
            if card.nid in seen_notes:
                continue
            seen_notes.add(card.nid)
            note = card.note()
            _set_event_tag(note, prefix, date_str)
            mw.col.update_note(note)
        except Exception as e:
            print(f"SuspensionTracker error: {e}")

def _fetch_suspended_ids() -> set[int]:
    try:
        return set(mw.col.db.list("SELECT id FROM cards WHERE queue = -1"))
    except:
        return set()

def _load_snapshot() -> None:
    global _suspended_snapshot, _snapshot_loaded
    if not mw.col:
        return
    _suspended_snapshot = _fetch_suspended_ids()
    _snapshot_loaded = True

def _on_operation_did_execute(changes, handler=None) -> None:
    global _suspended_snapshot, _snapshot_loaded

    if not _snapshot_loaded:
        _load_snapshot()

    if not getattr(changes, "study_queues", False):
        return

    current = _fetch_suspended_ids()
    new_sus = current - _suspended_snapshot
    new_unsus = _suspended_snapshot - current

    if new_sus or new_unsus:
        today = datetime.date.today().isoformat()
        if new_sus:
            _stamp_notes(list(new_sus), TAG_SUSPEND, today)
        if new_unsus:
            _stamp_notes(list(new_unsus), TAG_UNSUSPEND, today)

    _suspended_snapshot = current

def _in_range(date_str: str, start: str, end: str) -> bool:
    try:
        d = datetime.date.fromisoformat(date_str)
        if start != "*" and d < datetime.date.fromisoformat(start):
            return False
        if end != "*" and d > datetime.date.fromisoformat(end):
            return False
        return True
    except:
        return False

def _find_notes_in_range(tag_prefix: str, start: str, end: str) -> set[int]:
    results = set()
    try:
        rows = mw.col.db.all(
            "SELECT id, tags FROM notes WHERE tags LIKE ?",
            f"%{tag_prefix}::%",
        )
        for nid, tags_str in rows:
            for tag in tags_str.split():
                if tag.startswith(f"{tag_prefix}::"):
                    date_val = tag[len(f"{tag_prefix}::"):]
                    if _in_range(date_val, start, end):
                        results.add(nid)
                    break
    except:
        pass
    return results

def _on_browser_will_search(ctx) -> None:
    # remove old tokens
    match = re.search(rf'\btracker:(unsuspended|suspended):({_DATE_REGEX}):({_DATE_REGEX})\b', ctx.search, re.I)
    if not match:
        return

    event, start, end = match.group(1).lower(), match.group(2), match.group(3)
    prefix = EVENT_MAP.get(event)
    if not prefix:
        return

    nids = _find_notes_in_range(prefix, start, end)
    if nids:
        nid_str = ",".join(str(n) for n in nids)
        cids = set(mw.col.db.list(f"SELECT id FROM cards WHERE nid IN ({nid_str})"))
    else:
        cids = set()

    remaining = re.sub(rf'\btracker:(unsuspended|suspended):({_DATE_REGEX}):({_DATE_REGEX})\b', "", ctx.search, flags=re.I).strip()
    if remaining:
        try:
            found = set(mw.col.find_cards(remaining))
            final = cids & found
        except:
            final = cids
    else:
        final = cids

    ctx.card_ids = list(final)

# Browser UI
_COLUMNS = [
    ("suspension_tracker_unsuspended", "Unsuspended", TAG_UNSUSPEND),
    ("suspension_tracker_suspended", "Suspended", TAG_SUSPEND),
]

def _on_browser_did_fetch_columns(columns: dict) -> None:
    if not HAS_BROWSER_COLUMNS:
        return
    for key, label, _ in _COLUMNS:
        col = BrowserColumns.Column()
        col.key = key
        col.cards_mode_label = label
        col.notes_mode_label = label
        col.alignment = BrowserColumns.ALIGNMENT_CENTER
        columns[col.key] = col

def _on_browser_did_fetch_row(id, is_note, row, columns) -> None:
    for key, _, prefix in _COLUMNS:
        if key not in columns:
            continue
        idx = list(columns).index(key)
        try:
            item = mw.col.get_note(id) if is_note else mw.col.get_card(id).note()
            row.cells[idx].text = _get_event_date(item, prefix)
        except:
            row.cells[idx].text = ""

def _inject_search(current_search: str, new_token: str) -> str:
    term_pattern = re.compile(
        rf'\b(?:tag:{NS}::(?:unsuspended|suspended)::[\d\-*]+|tracker:(?:unsuspended|suspended):{_DATE_REGEX}:{_DATE_REGEX})\b',
        re.I
    )
    
    # split by OR
    parts = re.split(r'\s+OR\s+', current_search, flags=re.I)
    cleaned_parts = [p for p in parts if not term_pattern.search(p)]
    
    final_base = " OR ".join(cleaned_parts).strip()
    
    final_base = term_pattern.sub("", final_base).strip()
    
    if not final_base:
        return new_token
    return f"{final_base} {new_token}"

def _open_tracker_dialog(browser) -> None:
    dialog = DateRangeDialog(browser)
    if dialog.exec():
        new_token = dialog.get_search_string()
        if new_token:
            search_edit = getattr(browser.form, "searchEdit", getattr(browser.form, "search_edit", None))
            if search_edit:
                # QComboBox vs QLineEdit
                if hasattr(search_edit, "setEditText"):
                    current_search = search_edit.currentText()
                    updated_search = _inject_search(current_search, new_token)
                    search_edit.setEditText(updated_search)
                else:
                    current_search = search_edit.text()
                    updated_search = _inject_search(current_search, new_token)
                    search_edit.setText(updated_search)
                browser.onSearchActivated()

def _on_browser_menus_did_init(browser) -> None:
    # menu action
    action = QAction("Search Suspensions by Date...", browser)
    action.triggered.connect(lambda _, b=browser: _open_tracker_dialog(b))
    
    # variable menu names
    for attr in ["menu_Search", "menuSearch", "menu_Cards", "menuCards", "menu_Notes", "menuNotes"]:
        menu = getattr(browser.form, attr, None)
        if menu:
            menu.addAction(action)
            break

# Hooks
gui_hooks.profile_did_open.append(_load_snapshot)
gui_hooks.operation_did_execute.append(_on_operation_did_execute)
gui_hooks.browser_will_search.append(_on_browser_will_search)
gui_hooks.browser_menus_did_init.append(_on_browser_menus_did_init)

if HAS_BROWSER_COLUMNS:
    gui_hooks.browser_did_fetch_columns.append(_on_browser_did_fetch_columns)
    gui_hooks.browser_did_fetch_row.append(_on_browser_did_fetch_row)
