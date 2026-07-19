#!/usr/bin/env python3
"""Shop Bot — No Emoji, Auto OOS, Reseller System"""

import asyncio
import json
import logging
import os
import re
import signal
import subprocess
import uuid
from datetime import datetime
from pathlib import Path

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, BotCommand, MenuButtonCommands
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters,
    PicklePersistence
)
from telegram.error import Conflict, NetworkError, TimedOut

logging.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════════════
BOT_TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN", os.environ.get("BOT_TOKEN", ""))
OWNER_IDS   = [8503115617, 8496889757]
DATA_FILE   = "bot_data.json"
UPI_QR_FILE = "upi_qr.jpg"

# ═══════════════════════════════════════════════════════════════════
#  MENU
# ═══════════════════════════════════════════════════════════════════
MENU: dict = {
    "ff_ios": {
        "label": "Free Fire (iOS)",
        "products": [
            {"name": "Fluorite",    "prices": [("31 Days","23.00"),("7 Days","15.00"),("1 Day","5.00")]},
            {"name": "Migul PRO",   "prices": [("31 Days","20.00"),("7 Days","10.00"),("1 Day","3.00")]},
            {"name": "iMAZING",     "prices": [("31 Days","9.00")]},
        ],
    },
    "ff_and": {
        "label": "Free Fire (Android)",
        "products": [
            {"name": "HG-Cheats Root",      "prices": [("31 Days","13.00"),("10 Days","6.50"),("7 Days","5.50"),("1 Day","4.00")]},
            {"name": "HG-Cheats Non-Root",  "prices": [("31 Days","13.00"),("10 Days","8.00"),("7 Days","5.50"),("1 Day","4.00")]},
            {"name": "PatoTeam Non-Root",   "prices": [("31 Days","12.50"),("15 Days","8.50"),("7 Days","6.00"),("1 Day","2.50")]},
            {"name": "Drip-Client Root",    "prices": [("31 Days","12.00"),("15 Days","8.00"),("7 Days","4.50"),("1 Day","2.00")]},
            {"name": "Drip-Client Non-Root","prices": [("31 Days","12.00"),("15 Days","8.00"),("7 Days","4.50"),("1 Day","2.00")]},
        ],
    },
    "8b_ios": {
        "label": "8 Ball Pool (iOS)",
        "products": [
            {"name": "Wizard iOS",          "prices": [("30 Days","18.00"),("7 Days","8.00"),("1 Day","2.00")]},
            {"name": "Star Wolf GBD Pixel", "prices": [("30 Days","12.00"),("7 Days","5.50"),("1 Day","2.00")]},
            {"name": "iOS-Viet",            "prices": [("30 Days","20.00"),("7 Days","10.00"),("1 Day","4.00")]},
            {"name": "Potassium iOS",       "prices": [("30 Days","14.00"),("7 Days","8.00"),("1 Day","4.00")]},
        ],
    },
    "8b_and": {
        "label": "8 Ball Pool (Android)",
        "products": [],
    },
    "cert_ios": {
        "label": "Certificate (iOS)",
        "is_cert": True,
        "products": [
            {"name": "iPhone Certificate", "prices": [("300 Days","10.00")]},
            {"name": "iPad Certificate",   "prices": [("300 Days","10.00")]},
        ],
    },
    "ml_ios": {
        "label": "Mobile Legends (iOS)",
        "products": [
            {"name": "Fluorite MLBB", "prices": [("30 Days","23.00"),("7 Days","15.00"),("1 Day","5.00")]},
        ],
    },
    "pubg_ios": {
        "label": "PUBG Mobile (iOS)",
        "products": [
            {"name": "Dolphin iOS",  "prices": [("30 Days","14.00"),("7 Days","8.00"),("1 Day","3.50")]},
            {"name": "Star Win iOS", "prices": [("30 Days","15.00"),("7 Days","8.00"),("1 Day","3.50")]},
            {"name": "GroX iOS",     "prices": [("30 Days","18.00"),("7 Days","12.00"),("1 Day","6.00")]},
        ],
    },
    "pubg_and": {
        "label": "PUBG Mobile (Android)",
        "products": [
            {"name": "Zolo Non-Root", "prices": [("30 Days","15.00"),("7 Days","6.00"),("1 Day","2.00")]},
            {"name": "aXel PM",       "prices": [("30 Days","20.00"),("7 Days","12.00"),("1 Day","6.00")]},
            {"name": "Fluxo SRS",     "prices": [("30 Days","20.00"),("7 Days","12.00"),("1 Day","6.00")]},
        ],
    },
}
BUILTIN_CAT_ORDER = ["ff_ios","ff_and","8b_ios","8b_and","cert_ios","ml_ios","pubg_ios","pubg_and"]
CAT_ORDER: list   = list(BUILTIN_CAT_ORDER)
_CUSTOM_KEYS: set = set()

# ── Stock display emojis ───────────────────────────────────────────
STOCK_HEADER_EMOJI = "5323289282499064033"
STOCK_IN_EMOJI     = "5445195276291693508"
STOCK_OUT_EMOJI    = "6260156709298250200"

CAT_EMOJI: dict = {
    "ff_ios":    "6226587128948595866",
    "ff_and":    "6226587128948595866",
    "8b_ios":    "5798859315989191720",
    "8b_and":    "5798859315989191720",
    "cert_ios":  "6226499618989940625",
    "ml_ios":    "6233005983342272275",
    "pubg_ios":  "5803015182179375847",
    "pubg_and":  "5803015182179375847",
}

PROD_EMOJI: dict = {
    "Fluorite":              "5292158397465005457",
    "Migul PRO":             "6161366096348716597",
    "iMAZING":               "6262508891087577197",
    "HG-Cheats Root":        "6210499577322151683",
    "HG-Cheats Non-Root":    "6210499577322151683",
    "PatoTeam Non-Root":     "6210656322153618819",
    "Drip-Client Root":      "6212942266957310140",
    "Drip-Client Non-Root":  "6212942266957310140",
    "Wizard iOS":            "5798859315989191720",
    "Star Wolf GBD Pixel":   "5798859315989191720",
    "iOS-Viet":              "5798859315989191720",
    "Potassium iOS":         "5798859315989191720",
    "iPhone Certificate":    "6017150732455646343",
    "iPad Certificate":      "6017150732455646343",
    "Fluorite MLBB":         "5292158397465005457",
    "Dolphin iOS":           "5803015182179375847",
    "Star Win iOS":          "5803015182179375847",
    "GroX iOS":              "5803015182179375847",
    "Zolo Non-Root":         "5803015182179375847",
    "aXel PM":               "5803015182179375847",
    "Fluxo SRS":             "5803015182179375847",
}

def stock_ce(emoji_id: str, fallback: str = "▪") -> str:
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

def merge_custom_cats(d: dict):
    global _CUSTOM_KEYS
    for k in list(_CUSTOM_KEYS):
        MENU.pop(k, None)
        if k in CAT_ORDER:
            CAT_ORDER.remove(k)
    _CUSTOM_KEYS = set()
    for cat_data in d.get("custom_cats", []):
        key = cat_data["key"]
        MENU[key] = {
            "label":   cat_data["label"],
            "custom":  True,
            "products": [
                {"name": p["name"], "prices": [tuple(pr) for pr in p["prices"]]}
                for p in cat_data.get("products", [])
            ]
        }
        if key not in CAT_ORDER:
            CAT_ORDER.append(key)
        _CUSTOM_KEYS.add(key)

# ═══════════════════════════════════════════════════════════════════
#  CUSTOM EMOJI
# ═══════════════════════════════════════════════════════════════════
def ce(emoji_id: str, fallback: str = "▪") -> str:
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

CE_WELCOME   = ce("5256131095094652290", "👋")
CE_SHOP_TAP  = ce("5440841102871517055", "🛒")
CE_SELECT    = ce("5440841102871517055", "📂")
CE_SUMMARY   = ce("6037475557082403885", "🧾")
CE_PRODUCT   = ce("5886473311637999700", "📦")
CE_PLAN      = ce("5775896410780079073", "📅")
CE_QTY       = ce("5884479287171485878", "🔢")
CE_PRICE     = ce("5904462880941545555", "💰")
CE_KEY       = ce("6005570495603282482", "🔑")
CE_ACCT      = ce("5904630315946611415", "👤")
CE_ANIM      = ce("4911178215441040907", "✅")
CE_BAN       = ce("5447644880824181073", "🚫")
CE_NEWUSER   = ce("5226711870492126462", "🟢")

# ═══════════════════════════════════════════════════════════════════
#  DATA HELPERS
# ═══════════════════════════════════════════════════════════════════
_MEM_DATA:  dict = {}
_MEM_STATE: dict = {}

SETTINGS_DEFAULTS = {
    "shop_name":       "My Shop",
    "support":         "@NyraHere",
    "binance_id":      "000000000",
    "upi_qr_file_id":  None,
}

def load() -> dict:
    global _MEM_DATA
    d = None
    if Path(DATA_FILE).exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            pass
    if d is None:
        d = dict(_MEM_DATA) if _MEM_DATA else {}
    d.setdefault("verified",         [])
    d.setdefault("admin_ids",        [])
    d.setdefault("keys",             {})
    d.setdefault("files",            {})
    d.setdefault("balances",         {})
    d.setdefault("pending_orders",   {})
    d.setdefault("purchase_history", {})
    d.setdefault("custom_cats",      [])
    d.setdefault("price_overrides",  {})
    d.setdefault("reseller_prices",  {})
    d.setdefault("resellers",        {})
    d.setdefault("banned_users",     [])
    d.setdefault("all_users",        {})
    d.setdefault("balance_history",  {})
    d.setdefault("_state",           {})
    s = d.setdefault("settings",     {})
    for k, v in SETTINGS_DEFAULTS.items():
        s.setdefault(k, v)
    merge_custom_cats(d)
    return d

def save(d: dict):
    global _MEM_DATA
    _MEM_DATA = d
    tmp = DATA_FILE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2, ensure_ascii=False)
        os.replace(tmp, DATA_FILE)
    except Exception:
        pass

def get_state(d: dict, uid: int):
    key = str(uid)
    return d.get("_state", {}).get(key) or _MEM_STATE.get(key)

def set_state(d: dict, uid: int, state):
    key = str(uid)
    _MEM_STATE[key] = state
    d.setdefault("_state", {})[key] = state
    save(d)

def clear_state(d: dict, uid: int):
    key = str(uid)
    _MEM_STATE.pop(key, None)
    d.setdefault("_state", {}).pop(key, None)
    save(d)

def is_owner(uid: int) -> bool:
    return uid in OWNER_IDS

def is_admin(uid: int, d: dict) -> bool:
    return uid in OWNER_IDS or uid in d.get("admin_ids", [])

def is_verified(uid: int, d: dict) -> bool:
    return is_admin(uid, d) or uid in d.get("verified", [])

def get_balance(uid: int, d: dict) -> float:
    return round(float(d.get("balances", {}).get(str(uid), 0.0)), 2)

def add_balance_tx(uid: int, amount: float, note: str, d: dict):
    entry = {
        "amount": round(amount, 2),
        "note":   note,
        "date":   datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    }
    hist = d.setdefault("balance_history", {}).setdefault(str(uid), [])
    hist.append(entry)
    if len(hist) > 100:
        d["balance_history"][str(uid)] = hist[-100:]
    save(d)

def get_balance_tx_history(uid: int, d: dict) -> list:
    return d.get("balance_history", {}).get(str(uid), [])

def is_reseller(uid: int, d: dict) -> bool:
    return str(uid) in d.get("resellers", {})

def is_banned(uid: int, d: dict) -> bool:
    return uid in d.get("banned_users", [])

def track_user(uid: int, user, d: dict):
    existing = d.setdefault("all_users", {}).get(str(uid), {})
    d["all_users"][str(uid)] = {
        "name":     user.full_name or "N/A",
        "username": user.username or "",
        "joined":   existing.get("joined", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")),
    }
    save(d)

def get_reseller_price(k: str, idx: int, dur: str, d: dict):
    return d.get("reseller_prices", {}).get(f"{k}_{idx}_{dur}")

# ─── Key / File slot helpers ──────────────────────────────────────
def key_slot(cat: str, idx: int, dur: str) -> str:
    return f"{cat}_{idx}_{dur}"

def file_slot(cat: str, idx: int) -> str:
    return f"file_{cat}_{idx}"

def keys_count(cat: str, idx: int, dur: str, d: dict) -> int:
    return len(d.get("keys", {}).get(key_slot(cat, idx, dur), []))

def slot_stock(cat: str, idx: int, dur: str, d: dict) -> int:
    return keys_count(cat, idx, dur, d)

def total_product_stock(k: str, i: int, d: dict) -> int:
    cat = MENU.get(k, {})
    prods = cat.get("products", [])
    if i >= len(prods): return 0
    return sum(slot_stock(k, i, dur, d) for dur, _ in prods[i]["prices"])

def pop_key(cat: str, idx: int, dur: str, d: dict):
    slot = key_slot(cat, idx, dur)
    lst  = d.get("keys", {}).get(slot, [])
    if not lst: return None
    k = lst.pop(0)
    d["keys"][slot] = lst
    save(d)
    return k

def has_file(cat: str, idx: int, d: dict) -> bool:
    return file_slot(cat, idx) in d.get("files", {}) and d["files"][file_slot(cat, idx)] is not None

def get_file(cat: str, idx: int, d: dict):
    return d.get("files", {}).get(file_slot(cat, idx))

def set_file_data(cat: str, idx: int, file_item: dict, d: dict):
    d.setdefault("files", {})[file_slot(cat, idx)] = file_item
    save(d)

def remove_file_data(cat: str, idx: int, d: dict):
    d.setdefault("files", {}).pop(file_slot(cat, idx), None)
    save(d)

# ─── Auto OOS helpers ─────────────────────────────────────────────
def cat_has_stock(k: str, d: dict) -> bool:
    cat = MENU.get(k, {})
    if not cat.get("products"):
        return False
    if cat.get("is_cert"):
        for i in range(len(cat.get("products", []))):
            if has_file(k, i, d):
                return True
        return False
    for i, p in enumerate(cat.get("products", [])):
        for dur, _ in p["prices"]:
            if slot_stock(k, i, dur, d) > 0:
                return True
    return False

def cat_is_oos(k: str, d: dict) -> bool:
    cat = MENU.get(k, {})
    if cat.get("out_of_stock"):
        return True
    return not cat_has_stock(k, d)

# ─── Price helpers ────────────────────────────────────────────────
def reseller_price_key(k: str, idx: int, dur: str) -> str:
    return f"{k}_{idx}_{dur}"

def get_base_price(k: str, idx: int, dur: str, d: dict) -> str:
    override_key = f"{k}_{idx}_{dur}"
    ovr = d.get("price_overrides", {}).get(override_key)
    if ovr is not None:
        return ovr
    cat = MENU.get(k, {})
    prods = cat.get("products", [])
    if idx >= len(prods): return "0.00"
    for (d_dur, d_price) in prods[idx]["prices"]:
        if d_dur == dur:
            return d_price
    return "0.00"

def get_reseller_price(k: str, idx: int, dur: str, d: dict) -> str:
    rkey = reseller_price_key(k, idx, dur)
    rp = d.get("reseller_prices", {}).get(rkey)
    if rp is not None:
        return rp
    return None

def get_user_price(k: str, idx: int, dur: str, uid: int, d: dict) -> str:
    if is_reseller(uid, d):
        rp = get_reseller_price(k, idx, dur, d)
        if rp is not None:
            return rp
    return get_base_price(k, idx, dur, d)

def get_product_prices_for_user(k: str, idx: int, uid: int, d: dict) -> list:
    cat = MENU.get(k, {})
    prods = cat.get("products", [])
    if idx >= len(prods): return []
    result = []
    for (dur, _) in prods[idx]["prices"]:
        price = get_user_price(k, idx, dur, uid, d)
        result.append((dur, price))
    return result

# ─── Purchase history ─────────────────────────────────────────────
def add_purchase(uid: int, product_name: str, duration: str, price: str, method: str, d: dict, username: str = ""):
    d.setdefault("purchase_history", {}).setdefault(str(uid), [])
    entry = {
        "product":  product_name,
        "duration": duration,
        "price":    price,
        "method":   method,
        "date":     datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "username": username,
    }
    d["purchase_history"][str(uid)].append(entry)
    if len(d["purchase_history"][str(uid)]) > 50:
        d["purchase_history"][str(uid)] = d["purchase_history"][str(uid)][-50:]
    save(d)

def get_purchase_history(uid: int, d: dict) -> list:
    return d.get("purchase_history", {}).get(str(uid), [])

# ─── Misc helpers ─────────────────────────────────────────────────
def esc(t) -> str:
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def shop_name(d: dict) -> str:
    return d.get("settings", {}).get("shop_name", "My Shop")

def support_contact(d: dict) -> str:
    return d.get("settings", {}).get("support", "@support")

def binance_id(d: dict) -> str:
    return d.get("settings", {}).get("binance_id", "000000000")

def parse_product_line(line: str):
    parts = [p.strip() for p in line.split("|")]
    if len(parts) < 2: return None
    name = parts[0].strip()
    if not name: return None
    prices = []
    for part in parts[1:]:
        tokens = part.strip().rsplit(" ", 1)
        if len(tokens) != 2: return None
        dur, price = tokens[0].strip(), tokens[1].strip()
        try: float(price)
        except ValueError: return None
        if not dur: return None
        prices.append((dur, price))
    return (name, prices) if prices else None

async def send_long(target, text: str, **kwargs):
    limit = 4096
    if len(text) <= limit:
        await target.reply_text(text, **kwargs)
        return
    chunks, current = [], ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > limit:
            chunks.append(current)
            current = line
        else:
            current = current + "\n" + line if current else line
    if current: chunks.append(current)
    for chunk in chunks:
        await target.reply_text(chunk, **kwargs)
        await asyncio.sleep(0.15)

# ═══════════════════════════════════════════════════════════════════
#  KEYBOARDS
# ═══════════════════════════════════════════════════════════════════
def kb_main(uid: int, d: dict) -> ReplyKeyboardMarkup:
    rows = [["Shop"], ["Account", "Stock"], ["Support"]]
    if is_admin(uid, d):
        rows.append(["Admin Panel"])
    if is_reseller(uid, d) and not is_admin(uid, d):
        rows.append(["Reseller Shop", "Reseller Panel"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

def kb_verify() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("Verify Access", callback_data="verify")
    ]])

def kb_cats(uid: int, d: dict, reseller_mode: bool = False) -> InlineKeyboardMarkup:
    rows = []
    for k in CAT_ORDER:
        cat   = MENU.get(k, {})
        label = cat.get("label", k)
        if cat_is_oos(k, d):
            label += "  [Out of Stock]"
        rows.append([InlineKeyboardButton(label, callback_data=f"cat|{k}|{'r' if reseller_mode else 'u'}")])
    return InlineKeyboardMarkup(rows)

def kb_cat(k: str, reseller_mode: bool = False) -> InlineKeyboardMarkup:
    mode = "r" if reseller_mode else "u"
    rows = [
        [InlineKeyboardButton(p["name"], callback_data=f"prod|{k}|{i}|{mode}")]
        for i, p in enumerate(MENU[k]["products"])
    ]
    rows.append([InlineKeyboardButton("Back", callback_data=f"cats|{mode}")])
    return InlineKeyboardMarkup(rows)

def kb_durations(k: str, idx: int, uid: int, d: dict, reseller_mode: bool = False) -> InlineKeyboardMarkup:
    prices = get_product_prices_for_user(k, idx, uid, d)
    mode = "r" if reseller_mode else "u"
    rows = []
    for dur, price in prices:
        qty    = slot_stock(k, idx, dur, d)
        status = "[IN STOCK]" if qty > 0 else "[OUT]"
        label  = f"{status}  {dur}  -  ${price}"
        rows.append([InlineKeyboardButton(label, callback_data=f"dur|{k}|{idx}|{dur}|{price}|{mode}")])
    rows.append([InlineKeyboardButton("Back", callback_data=f"prod_back|{k}|{mode}")])
    return InlineKeyboardMarkup(rows)

def kb_payment(k: str, idx: int, dur: str, price: str, uid: int, d: dict, mode: str = "u") -> InlineKeyboardMarkup:
    base = f"{k}|{idx}|{dur}|{price}|{mode}"
    rows = [
        [InlineKeyboardButton("Pay via UPI",     callback_data=f"pay|upi|{base}")],
        [InlineKeyboardButton("Pay via Binance", callback_data=f"pay|bnb|{base}")],
        [InlineKeyboardButton("Other Method",    callback_data=f"pay|other|{base}")],
    ]
    bal = get_balance(uid, d)
    try: price_f = float(price)
    except ValueError: price_f = 9999.0
    if bal >= price_f:
        rows.insert(0, [InlineKeyboardButton(
            f"Pay with Balance  (${bal:.2f})",
            callback_data=f"pay|bal|{base}"
        )])
    rows.append([InlineKeyboardButton("Back", callback_data=f"dur|{k}|{idx}|{dur}|{price}|{mode}")])
    return InlineKeyboardMarkup(rows)

def kb_paid(k: str, idx: int, dur: str, price: str, method: str, mode: str = "u") -> InlineKeyboardMarkup:
    base = f"{k}|{idx}|{dur}|{price}|{method}|{mode}"
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("I've Sent Payment", callback_data=f"paid|{base}")
    ]])

def kb_account() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Purchase History",  callback_data="acc|history")],
        [InlineKeyboardButton("Balance History",   callback_data="acc|bal_history")],
    ])

def kb_admin() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Add Keys",          callback_data="adm|add_keys"),
         InlineKeyboardButton("Add/Replace File",  callback_data="adm|add_files")],
        [InlineKeyboardButton("View Keys Stock",   callback_data="adm|view_keys"),
         InlineKeyboardButton("View Files Stock",  callback_data="adm|view_files")],
        [InlineKeyboardButton("Remove File",       callback_data="adm|remove_file"),
         InlineKeyboardButton("Clear Keys",        callback_data="adm|clear")],
        [InlineKeyboardButton("Add Balance",       callback_data="adm|add_bal"),
         InlineKeyboardButton("Deduct Balance",    callback_data="adm|ded_bal")],
        [InlineKeyboardButton("Check Balance",     callback_data="adm|chk_bal"),
         InlineKeyboardButton("Add Admin",         callback_data="adm|add_admin")],
        [InlineKeyboardButton("Add Category",      callback_data="adm|add_cat"),
         InlineKeyboardButton("Del Category",      callback_data="adm|del_cat")],
        [InlineKeyboardButton("Edit Price",        callback_data="adm|edit_price"),
         InlineKeyboardButton("Pending Orders",    callback_data="adm|pending")],
        [InlineKeyboardButton("Broadcast",         callback_data="adm|broadcast"),
         InlineKeyboardButton("Set UPI QR",        callback_data="adm|set_upi_qr")],
        [InlineKeyboardButton("Set Binance ID",    callback_data="adm|set_bnb_id"),
         InlineKeyboardButton("Set Support",       callback_data="adm|set_support")],
        [InlineKeyboardButton("Set Shop Name",     callback_data="adm|set_shop_name")],
        [InlineKeyboardButton("--- RESELLER MANAGEMENT ---", callback_data="adm|noop")],
        [InlineKeyboardButton("Add Reseller",      callback_data="adm|add_reseller"),
         InlineKeyboardButton("Remove Reseller",   callback_data="adm|rem_reseller")],
        [InlineKeyboardButton("View Resellers",    callback_data="adm|view_resellers"),
         InlineKeyboardButton("Edit Reseller Prices", callback_data="adm|edit_reseller_price")],
        [InlineKeyboardButton("--- USER MANAGEMENT ---",    callback_data="adm|noop")],
        [InlineKeyboardButton("View All Users",    callback_data="adm|view_users"),
         InlineKeyboardButton("Ban User",          callback_data="adm|ban_user")],
        [InlineKeyboardButton("Unban User",        callback_data="adm|unban_user")],
    ])

def kb_approve_deny(order_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("Approve", callback_data=f"approve|{order_id}"),
        InlineKeyboardButton("Deny",    callback_data=f"deny|{order_id}"),
    ]])

def kb_adm_cats_keys() -> InlineKeyboardMarkup:
    rows = []
    for k in CAT_ORDER:
        cat = MENU.get(k, {})
        if not cat.get("products"): continue
        rows.append([InlineKeyboardButton(cat["label"], callback_data=f"akc|{k}")])
    rows.append([InlineKeyboardButton("Cancel", callback_data="adm|cancel")])
    return InlineKeyboardMarkup(rows)

def kb_adm_cats_files(mode: str) -> InlineKeyboardMarkup:
    rows = []
    for k in CAT_ORDER:
        cat = MENU.get(k, {})
        if not cat.get("products"): continue
        rows.append([InlineKeyboardButton(cat["label"], callback_data=f"a{mode}c|{k}")])
    rows.append([InlineKeyboardButton("Cancel", callback_data="adm|cancel")])
    return InlineKeyboardMarkup(rows)

def kb_adm_prods_keys(cat_key: str) -> InlineKeyboardMarkup:
    cat  = MENU.get(cat_key, {})
    rows = [[InlineKeyboardButton(p["name"], callback_data=f"akp|{cat_key}|{i}")]
            for i, p in enumerate(cat.get("products", []))]
    rows.append([InlineKeyboardButton("Back", callback_data="adm|add_keys")])
    return InlineKeyboardMarkup(rows)

def kb_adm_prods_files(mode: str, cat_key: str) -> InlineKeyboardMarkup:
    cat  = MENU.get(cat_key, {})
    rows = [[InlineKeyboardButton(p["name"], callback_data=f"a{mode}p|{cat_key}|{i}")]
            for i, p in enumerate(cat.get("products", []))]
    back = "add_files" if mode == "f" else "remove_file"
    rows.append([InlineKeyboardButton("Back", callback_data=f"adm|{back}")])
    return InlineKeyboardMarkup(rows)

def kb_adm_durs_keys(cat_key: str, idx: int) -> InlineKeyboardMarkup:
    prod = MENU[cat_key]["products"][idx]
    rows = []
    for dur, _ in prod["prices"]:
        dur_enc = dur.replace(" ", "~")
        rows.append([InlineKeyboardButton(dur, callback_data=f"akd|{cat_key}|{idx}|{dur_enc}")])
    rows.append([InlineKeyboardButton("Back", callback_data=f"akc|{cat_key}")])
    return InlineKeyboardMarkup(rows)

def kb_adm_cats_price() -> InlineKeyboardMarkup:
    rows = []
    for k in CAT_ORDER:
        cat = MENU.get(k, {})
        if not cat.get("products"): continue
        rows.append([InlineKeyboardButton(cat["label"], callback_data=f"epc|{k}")])
    rows.append([InlineKeyboardButton("Cancel", callback_data="adm|cancel")])
    return InlineKeyboardMarkup(rows)

def kb_adm_prods_price(cat_key: str) -> InlineKeyboardMarkup:
    cat  = MENU.get(cat_key, {})
    rows = [[InlineKeyboardButton(p["name"], callback_data=f"epp|{cat_key}|{i}")]
            for i, p in enumerate(cat.get("products", []))]
    rows.append([InlineKeyboardButton("Back", callback_data="adm|edit_price")])
    return InlineKeyboardMarkup(rows)

def kb_adm_durs_price(cat_key: str, idx: int, d: dict) -> InlineKeyboardMarkup:
    prod = MENU.get(cat_key, {}).get("products", [])[idx]
    rows = []
    for dur, _ in prod["prices"]:
        cur = get_base_price(cat_key, idx, dur, d)
        dur_enc = dur.replace(" ", "~")
        rows.append([InlineKeyboardButton(
            f"{dur} - ${cur}",
            callback_data=f"epd|{cat_key}|{idx}|{dur_enc}"
        )])
    rows.append([InlineKeyboardButton("Back", callback_data=f"epc|{cat_key}")])
    return InlineKeyboardMarkup(rows)

# Reseller price keyboards
def kb_adm_cats_reseller_price() -> InlineKeyboardMarkup:
    rows = []
    for k in CAT_ORDER:
        cat = MENU.get(k, {})
        if not cat.get("products"): continue
        rows.append([InlineKeyboardButton(cat["label"], callback_data=f"erpc|{k}")])
    rows.append([InlineKeyboardButton("Cancel", callback_data="adm|cancel")])
    return InlineKeyboardMarkup(rows)

def kb_adm_prods_reseller_price(cat_key: str) -> InlineKeyboardMarkup:
    cat  = MENU.get(cat_key, {})
    rows = [[InlineKeyboardButton(p["name"], callback_data=f"erpp|{cat_key}|{i}")]
            for i, p in enumerate(cat.get("products", []))]
    rows.append([InlineKeyboardButton("Back", callback_data="adm|edit_reseller_price")])
    return InlineKeyboardMarkup(rows)

def kb_adm_durs_reseller_price(cat_key: str, idx: int, d: dict) -> InlineKeyboardMarkup:
    prod = MENU.get(cat_key, {}).get("products", [])[idx]
    rows = []
    for dur, _ in prod["prices"]:
        rp = get_reseller_price(cat_key, idx, dur, d)
        cur = f"${rp}" if rp else "(not set)"
        dur_enc = dur.replace(" ", "~")
        rows.append([InlineKeyboardButton(
            f"{dur} - {cur}",
            callback_data=f"erpd|{cat_key}|{idx}|{dur_enc}"
        )])
    rows.append([InlineKeyboardButton("Back", callback_data=f"erpc|{cat_key}")])
    return InlineKeyboardMarkup(rows)

def kb_del_custom_cats(d: dict) -> InlineKeyboardMarkup:
    rows = []
    for cat_data in d.get("custom_cats", []):
        key = cat_data["key"]
        rows.append([InlineKeyboardButton(
            cat_data['label'],
            callback_data=f"del_cat|{key}"
        )])
    rows.append([InlineKeyboardButton("Cancel", callback_data="adm|cancel")])
    return InlineKeyboardMarkup(rows)

def kb_list_resellers(d: dict) -> InlineKeyboardMarkup:
    rows = []
    for uid_str, info in d.get("resellers", {}).items():
        name = info.get("name", "")
        label = f"{uid_str}" + (f" — {esc(name)}" if name else "")
        rows.append([InlineKeyboardButton(label, callback_data=f"rem_res_confirm|{uid_str}")])
    rows.append([InlineKeyboardButton("Cancel", callback_data="adm|cancel")])
    return InlineKeyboardMarkup(rows)

# ═══════════════════════════════════════════════════════════════════
#  DISPLAY HELPERS
# ═══════════════════════════════════════════════════════════════════
def cat_msg(k: str, uid: int, d: dict, reseller_mode: bool = False) -> str:
    cat = MENU.get(k, {})
    if cat_is_oos(k, d):
        return (f"<b>{esc(cat['label'])}</b>\n\n"
                f"<b>Out of Stock</b>\n\nThis category is currently unavailable. Check back later!")
    return f"{CE_SELECT} <b>{esc(cat['label'])}</b>\n\nSelect a product:"

# ═══════════════════════════════════════════════════════════════════
#  VERIFY
# ═══════════════════════════════════════════════════════════════════
async def run_verify(query, uid: int, ctx: ContextTypes.DEFAULT_TYPE):
    msg = await query.message.reply_text(
        f"{CE_ANIM} <b>Verifying your access...</b>", parse_mode="HTML")
    await asyncio.sleep(2)
    try: await msg.edit_text(
        f"{CE_ANIM} <b>You are verified!</b>", parse_mode="HTML")
    except Exception: pass
    return msg, True

# ═══════════════════════════════════════════════════════════════════
#  PAYMENT DETAILS
# ═══════════════════════════════════════════════════════════════════
async def send_payment_details(message, k: str, idx: int, dur: str, price: str, method: str, d: dict, ctx, mode: str = "u"):
    prod = MENU[k]["products"][idx]
    order_text = (
        f"<b>Order:</b> {esc(prod['name'])}\n"
        f"<b>Duration:</b> {esc(dur)}\n"
        f"<b>Amount:</b> <b>${esc(price)}</b>"
    )
    paid_kb = kb_paid(k, idx, dur, price, method, mode)

    if method == "upi":
        fid = d.get("settings", {}).get("upi_qr_file_id")
        caption = (
            f"<b>Pay via UPI</b>\n\n{order_text}\n\n"
            f"Scan the QR and pay <b>${esc(price)}</b>.\n\nAfter paying, click the button below."
        )
        if fid:
            await message.reply_photo(photo=fid, caption=caption, parse_mode="HTML", reply_markup=paid_kb)
        elif Path(UPI_QR_FILE).exists():
            with open(UPI_QR_FILE, "rb") as f:
                sent = await message.reply_photo(photo=f, caption=caption, parse_mode="HTML", reply_markup=paid_kb)
            try:
                new_fid = sent.photo[-1].file_id
                d["settings"]["upi_qr_file_id"] = new_fid
                save(d)
            except Exception: pass
        else:
            await message.reply_text(
                caption + f"\n\n<i>UPI QR not set. Contact admin.</i>\nSupport: {esc(support_contact(d))}",
                parse_mode="HTML", reply_markup=paid_kb)

    elif method == "bnb":
        bnb = binance_id(d)
        caption = (
            f"<b>Pay via Binance Pay</b>\n"
            f"---\n"
            f"{order_text}\n\n"
            f"Send <b>${esc(price)} USDT</b> to:\n"
            f"<b>Binance ID:</b> <code>{esc(bnb)}</code>\n"
            f"---\n"
            f"After sending, click the button below."
        )
        await message.reply_text(caption, parse_mode="HTML", reply_markup=paid_kb)

    else:
        await message.reply_text(
            f"<b>Other Payment Method</b>\n\n{order_text}\n\n"
            f"Contact our support team:\n{esc(support_contact(d))}", parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════════
#  DELIVER PRODUCT
# ═══════════════════════════════════════════════════════════════════
async def deliver_product(user_id: int, order: dict, ctx: ContextTypes.DEFAULT_TYPE) -> bool:
    k      = order["k"]
    i      = order["i"]
    dur    = order["dur"]
    price  = order["price"]
    method = order["method"]

    d   = load()
    cat = MENU.get(k)
    if not cat or i >= len(cat.get("products", [])): return False
    p = cat["products"][i]

    if keys_count(k, i, dur, d) == 0: return False

    key_val  = pop_key(k, i, dur, d)
    d2       = load()
    file_val = get_file(k, i, d2)

    method_label = {"upi": "UPI", "bnb": "Binance", "other": "Other", "bal": "Balance"}.get(method, method)
    sname = shop_name(d2)
    supp  = support_contact(d2)

    success_msg = (
        f"{CE_SUMMARY} <b>ORDER SUMMARY</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"— {CE_PRODUCT} <b>Product:</b> {esc(p['name'])}\n"
        f"— {CE_PLAN} <b>Plan:</b> {esc(dur)}\n"
        f"— {CE_QTY} <b>Quantity:</b> 1\n"
        f"— {CE_PRICE} <b>Unit price:</b> ${esc(price)}\n"
        f"— {CE_KEY} <b>Key:</b> <code>{esc(key_val)}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"NOTE: After completing the setup, open the game, enter your key, and send us a screenshot along with your feedback.\n\n"
        f"Support: {esc(supp)}"
    )
    await ctx.bot.send_message(chat_id=user_id, text=success_msg, parse_mode="HTML")

    if file_val:
        ftype  = file_val.get("type", "link")
        fvalue = file_val.get("value", "")
        fname  = file_val.get("name", "file")
        try:
            if ftype == "document":
                await ctx.bot.send_document(chat_id=user_id, document=fvalue,
                    caption=f"<b>{esc(fname)}</b>", parse_mode="HTML")
            elif ftype == "photo":
                await ctx.bot.send_photo(chat_id=user_id, photo=fvalue,
                    caption=f"<b>{esc(fname)}</b>", parse_mode="HTML")
            else:
                await ctx.bot.send_message(chat_id=user_id,
                    text=f"<b>Download Link:</b>\n{esc(fvalue)}", parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Could not send file to {user_id}: {e}")
    else:
        await ctx.bot.send_message(chat_id=user_id,
            text=f"<b>File coming soon.</b>\nContact admin: {esc(supp)}", parse_mode="HTML")

    d3 = load()
    order_uname = order.get("username", "")
    add_purchase(user_id, p["name"], dur, price, method_label, d3, username=order_uname)

    d4 = load()
    uname_display = f"@{esc(order_uname)}" if order_uname else f"ID: {user_id}"
    all_admins = list(set(OWNER_IDS + d4.get("admin_ids", [])))
    for aid in all_admins:
        try:
            file_note = (f"File: <b>{esc(file_val.get('name','?'))}</b>"
                         if file_val else "File: <b>not sent (none set)</b>")
            await ctx.bot.send_message(chat_id=aid,
                text=(f"<b>Purchase Approved and Delivered</b>\n\n"
                      f"User: <code>{user_id}</code>  ({uname_display})\n"
                      f"Product: {esc(p['name'])}\nDuration: {esc(dur)}\n"
                      f"Price: ${esc(price)}\nMethod: {method_label}\n"
                      f"Key: <code>{esc(key_val)}</code>\n{file_note}"),
                parse_mode="HTML")
        except Exception: pass
    return True

# ═══════════════════════════════════════════════════════════════════
#  COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════════════
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    d    = load()
    uid  = update.effective_user.id
    name = esc(update.effective_user.first_name or "there")
    if is_banned(uid, d):
        await update.message.reply_text(
            f"{CE_BAN} <b>You are banned from this bot.</b>\n\nContact support: {esc(support_contact(d))}",
            parse_mode="HTML")
        return
    track_user(uid, update.effective_user, d)
    clear_state(d, uid)
    sname = shop_name(d)
    if is_verified(uid, d):
        await update.message.reply_text(
            f"{CE_WELCOME} <b>Welcome back, {name}!</b>\n"
            f"We're so glad you're here!\n\n"
            f"Discover our latest collection of beautiful products at great prices. "
            f"Browse your favorites and find something you'll love.\n\n"
            f"{CE_SHOP_TAP} Click the <b>Shop</b> button to explore our collection and make your purchase.\n\n"
            f"Thank you for visiting, and happy shopping!",
            parse_mode="HTML", reply_markup=kb_main(uid, d))
    else:
        await update.message.reply_text(
            f"{CE_WELCOME} <b>Welcome to {esc(sname)}!</b>\n"
            f"We're so glad you're here!\n\n"
            f"Discover our latest collection of beautiful products at great prices. "
            f"Browse your favorites and find something you'll love.\n\n"
            f"{CE_SHOP_TAP} Press the button below to verify your access and start shopping.",
            parse_mode="HTML", reply_markup=kb_verify())

async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    d = load()
    await update.message.reply_text(
        "<b>Commands</b>\n\n/start - Main menu\n/help - This message\n\n"
        f"Support: {esc(support_contact(d))}", parse_mode="HTML")

async def cmd_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    d   = load()
    uid = update.effective_user.id
    if not is_admin(uid, d): return
    clear_state(d, uid)
    await update.message.reply_text(
        f"<b>Admin Panel - {esc(shop_name(d))}</b>",
        parse_mode="HTML", reply_markup=kb_admin())

async def cmd_addbal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    d   = load()
    uid = update.effective_user.id
    if not is_admin(uid, d): return
    args = ctx.args
    if len(args) != 2:
        await update.message.reply_text("Usage: /addbal USER_ID AMOUNT"); return
    try:
        tid = int(args[0]); amt = float(args[1])
        if amt <= 0: raise ValueError
    except ValueError:
        await update.message.reply_text("Invalid arguments."); return
    cur = get_balance(tid, d)
    d["balances"][str(tid)] = round(cur + amt, 2)
    save(d)
    add_balance_tx(tid, amt, f"Added by admin (via /addbal)", load())
    await update.message.reply_text(
        f"Added <b>${amt:.2f}</b> to <code>{tid}</code>.\nNew balance: <b>${cur+amt:.2f}</b>",
        parse_mode="HTML")

async def cmd_rembal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    d   = load()
    uid = update.effective_user.id
    if not is_admin(uid, d): return
    args = ctx.args
    if len(args) != 2:
        await update.message.reply_text("Usage: /rembal USER_ID AMOUNT"); return
    try:
        tid = int(args[0]); amt = float(args[1])
        if amt <= 0: raise ValueError
    except ValueError:
        await update.message.reply_text("Invalid arguments."); return
    cur = get_balance(tid, d)
    new = max(0.0, cur - amt)
    d["balances"][str(tid)] = round(new, 2)
    save(d)
    add_balance_tx(tid, -amt, f"Deducted by admin (via /rembal)", load())
    await update.message.reply_text(
        f"Deducted <b>${amt:.2f}</b> from <code>{tid}</code>.\nNew balance: <b>${new:.2f}</b>",
        parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════════
#  MEDIA HANDLER
# ═══════════════════════════════════════════════════════════════════
async def handle_media(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    d   = load()
    uid = update.effective_user.id

    if not is_verified(uid, d):
        await update.message.reply_text("Please verify first. Use /start", reply_markup=kb_verify())
        return

    state = get_state(d, uid)

    if state == "set_upi_qr" and is_admin(uid, d):
        photo = update.message.photo
        if not photo:
            await update.message.reply_text("Please send a photo for the UPI QR."); return
        fid = photo[-1].file_id
        try:
            f = await ctx.bot.get_file(fid)
            await f.download_to_drive(UPI_QR_FILE)
        except Exception: pass
        d["settings"]["upi_qr_file_id"] = fid
        save(d)
        clear_state(d, uid)
        await update.message.reply_text("UPI QR image updated!", reply_markup=kb_admin())
        return

    if state and state.startswith("add_file_item|") and is_admin(uid, d):
        parts = state.split("|", 3)
        if len(parts) != 3:
            await update.message.reply_text("Error. Use /start to reset."); return
        _, cat, idx_str = parts; idx = int(idx_str)
        if update.message.document:
            fobj      = update.message.document
            file_item = {"type": "document", "value": fobj.file_id, "name": fobj.file_name or "file"}
        elif update.message.photo:
            fobj      = update.message.photo[-1]
            file_item = {"type": "photo", "value": fobj.file_id, "name": "image"}
        else:
            await update.message.reply_text("Unsupported. Send a document or photo."); return
        set_file_data(cat, idx, file_item, d)
        clear_state(d, uid)
        prod_name = MENU[cat]["products"][idx]["name"] if idx < len(MENU[cat]["products"]) else f"#{idx}"
        await update.message.reply_text(
            f"<b>File Set!</b>\n\nProduct: <b>{esc(prod_name)}</b>\n"
            f"File: <b>{esc(file_item['name'])}</b>", parse_mode="HTML")
        return

    if state and state.startswith("waiting_ss|"):
        parts = state.split("|", 6)
        if len(parts) < 6:
            await update.message.reply_text("Error. Please try again."); return
        _, k, si, dur, price, method = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]
        mode = parts[6] if len(parts) > 6 else "u"
        i = int(si)
        if not (update.message.photo or update.message.document):
            await update.message.reply_text("Please send a screenshot (photo).")
            return
        cat = MENU.get(k)
        if not cat or i >= len(cat.get("products", [])):
            await update.message.reply_text("Invalid order. Please start over."); return
        p        = cat["products"][i]
        order_id = uuid.uuid4().hex[:12]
        uname_raw = update.effective_user.username or ""
        d["pending_orders"][order_id] = {"user_id": uid, "k": k, "i": i, "dur": dur, "price": price, "method": method, "username": uname_raw}
        save(d)
        clear_state(d, uid)
        method_label = {"upi": "UPI", "bnb": "Binance", "other": "Other"}.get(method, method)
        uname_display = f"@{esc(uname_raw)}" if uname_raw else f"ID: {uid}"
        user_info = (
            f"User: <code>{uid}</code>  ({uname_display})\nProduct: <b>{esc(p['name'])}</b>\n"
            f"Duration: <b>{esc(dur)}</b>\nPrice: <b>${esc(price)}</b>\n"
            f"Method: <b>{method_label}</b>\nOrder ID: <code>{order_id}</code>"
        )
        approve_kb = kb_approve_deny(order_id)
        all_admins = list(set(OWNER_IDS + d.get("admin_ids", [])))
        for aid in all_admins:
            try:
                if update.message.photo:
                    await ctx.bot.send_photo(chat_id=aid, photo=update.message.photo[-1].file_id,
                        caption=f"<b>Payment Screenshot</b>\n\n{user_info}",
                        parse_mode="HTML", reply_markup=approve_kb)
                else:
                    await ctx.bot.send_document(chat_id=aid, document=update.message.document.file_id,
                        caption=f"<b>Payment Screenshot</b>\n\n{user_info}",
                        parse_mode="HTML", reply_markup=approve_kb)
            except Exception as e:
                logger.warning(f"Could not notify admin {aid}: {e}")
        await update.message.reply_text(
            "<b>Screenshot received!</b>\n\nYour payment is being reviewed. "
            "You will receive your product after approval.", parse_mode="HTML")
        return

    if state and state.startswith("support_msg"):
        all_admins = list(set(OWNER_IDS + d.get("admin_ids", [])))
        user_tag   = f"@{update.effective_user.username}" if update.effective_user.username else f"ID {uid}"
        prefix     = f"<b>Support Request</b>\nFrom: {esc(user_tag)} (<code>{uid}</code>)\n\n"
        for aid in all_admins:
            try:
                if update.message.photo:
                    await ctx.bot.send_photo(chat_id=aid, photo=update.message.photo[-1].file_id,
                        caption=prefix + esc(update.message.caption or "(no caption)"), parse_mode="HTML")
                elif update.message.video:
                    await ctx.bot.send_video(chat_id=aid, video=update.message.video.file_id,
                        caption=prefix + esc(update.message.caption or "(no caption)"), parse_mode="HTML")
                elif update.message.document:
                    await ctx.bot.send_document(chat_id=aid, document=update.message.document.file_id,
                        caption=prefix + esc(update.message.caption or "(no caption)"), parse_mode="HTML")
            except Exception: pass
        clear_state(d, uid)
        await update.message.reply_text(
            "<b>Support message sent!</b>\n\nAn admin will get back to you soon.",
            parse_mode="HTML", reply_markup=kb_main(uid, d))
        return

    if not state:
        await update.message.reply_text("Use /start to open the main menu.")

# ═══════════════════════════════════════════════════════════════════
#  TEXT HANDLER
# ═══════════════════════════════════════════════════════════════════
async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    d    = load()
    uid  = update.effective_user.id
    text = (update.message.text or "").strip()

    if not is_verified(uid, d):
        await update.message.reply_text("Please verify your access first. Use /start",
                                        reply_markup=kb_verify())
        return

    if text in ("Shop", "Shop"):
        clear_state(d, uid)
        await update.message.reply_text(f"{CE_SELECT} <b>Select a category:</b>",
            parse_mode="HTML", reply_markup=kb_cats(uid, d, reseller_mode=False))
        return

    if text == "Reseller Shop":
        if not is_reseller(uid, d):
            await update.message.reply_text("You are not a reseller."); return
        clear_state(d, uid)
        await update.message.reply_text(f"{CE_SELECT} <b>Reseller Shop - Select a category:</b>",
            parse_mode="HTML", reply_markup=kb_cats(uid, d, reseller_mode=True))
        return

    if text in ("Account",):
        clear_state(d, uid)
        bal   = get_balance(uid, d)
        uname = update.effective_user.username or "N/A"
        hist  = get_purchase_history(uid, d)
        role  = ("Owner" if is_owner(uid) else
                 "Admin" if is_admin(uid, d) else
                 "Reseller" if is_reseller(uid, d) else "User")
        fname_display = esc(update.effective_user.full_name or 'N/A')
        uname_display = f"@{esc(uname)}" if uname != "N/A" else "N/A"
        await update.message.reply_text(
            f"{CE_ACCT} <b>ACCOUNT INFO</b>\n\n"
            f"<b>{fname_display}</b>\n"
            f"{uname_display} • ID: <code>{uid}</code>\n"
            f"Role: <b>{role}</b>\n"
            f"Balance: <b>${bal:.2f}</b>\n"
            f"Status: <b>Verified</b>\n"
            f"Purchases: <b>{len(hist)}</b>",
            parse_mode="HTML", reply_markup=kb_account())
        return

    if text in ("Stock",):
        clear_state(d, uid)
        hdr = stock_ce(STOCK_HEADER_EMOJI, "*")
        lines = [f"{hdr} <b>Stock Status</b>\n"]
        for k in CAT_ORDER:
            cat = MENU.get(k, {})
            if not cat.get("products") and not cat.get("is_cert"):
                continue
            cat_e = stock_ce(CAT_EMOJI.get(k, STOCK_HEADER_EMOJI), ".")
            lines.append(f"{cat_e} <b>{esc(cat['label'])}</b>")
            for i, p in enumerate(cat.get("products", [])):
                if cat.get("is_cert"):
                    has = has_file(k, i, d)
                    status_e = stock_ce(STOCK_IN_EMOJI, "+") if has else stock_ce(STOCK_OUT_EMOJI, "-")
                    total_str = "available" if has else "0 keys"
                else:
                    total = sum(keys_count(k, i, dur, d) for dur, _ in p["prices"])
                    status_e = stock_ce(STOCK_IN_EMOJI, "+") if total > 0 else stock_ce(STOCK_OUT_EMOJI, "-")
                    total_str = f"{total} keys"
                prod_e = stock_ce(PROD_EMOJI.get(p["name"], STOCK_OUT_EMOJI), ".")
                lines.append(f"{status_e} {prod_e} {esc(p['name'])} [{total_str}]")
            lines.append("")
        await send_long(update.message, "\n".join(lines), parse_mode="HTML")
        return

    if text in ("Support",):
        clear_state(d, uid)
        set_state(d, uid, "support_msg")
        await update.message.reply_text(
            "<b>Support</b>\n\nDescribe your issue.\nYou can send text, photo or video.\n\n"
            "Your message will be forwarded to our admins.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Cancel", callback_data="support_cancel")
            ]]))
        return

    if text in ("Admin Panel",):
        if not is_admin(uid, d):
            await update.message.reply_text("Admins only."); return
        clear_state(d, uid)
        await update.message.reply_text(
            f"<b>Admin Panel - {esc(shop_name(d))}</b>",
            parse_mode="HTML", reply_markup=kb_admin())
        return

    if text == "Reseller Panel":
        if not is_reseller(uid, d):
            await update.message.reply_text("You are not a reseller."); return
        clear_state(d, uid)
        bal = get_balance(uid, d)

        price_lines = []
        for k in CAT_ORDER:
            cat = MENU.get(k, {})
            if not cat.get("products"): continue
            has_rp = False
            cat_lines = [f"\n<b>{esc(cat['label'])}</b>"]
            for i, p in enumerate(cat.get("products", [])):
                for dur, _ in p["prices"]:
                    rp = get_reseller_price(k, i, dur, d)
                    if rp:
                        cat_lines.append(f"  {esc(p['name'])} - {esc(dur)}: <b>${rp}</b>")
                        has_rp = True
            if has_rp:
                price_lines.extend(cat_lines)

        rp_section = "\n".join(price_lines) if price_lines else "\n<i>No custom prices set yet.</i>"
        await update.message.reply_text(
            f"<b>Reseller Panel</b>\n\n"
            f"Balance: <b>${bal:.2f}</b>\n\n"
            f"<b>Your Prices:</b>{rp_section}\n\n"
            f"Use <b>Shop</b> to browse products.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Purchase History",  callback_data="acc|history")],
                [InlineKeyboardButton("Balance History",   callback_data="acc|bal_history")],
            ]))
        return

    # ── STATE MACHINE ──────────────────────────────────────────────
    state = get_state(d, uid)

    if state and state.startswith("support_msg"):
        all_admins = list(set(OWNER_IDS + d.get("admin_ids", [])))
        user_tag   = f"@{update.effective_user.username}" if update.effective_user.username else f"ID {uid}"
        for aid in all_admins:
            try:
                await ctx.bot.send_message(chat_id=aid,
                    text=(f"<b>Support Request</b>\n"
                          f"From: {esc(user_tag)} (<code>{uid}</code>)\n\n{esc(text)}"),
                    parse_mode="HTML")
            except Exception: pass
        clear_state(d, uid)
        await update.message.reply_text(
            "<b>Support message sent!</b>\n\nAn admin will get back to you soon.",
            parse_mode="HTML", reply_markup=kb_main(uid, d))
        return

    if state == "newcat_name" and is_admin(uid, d):
        if not text or len(text) > 80:
            await update.message.reply_text("Name too short or long. Try again:"); return
        set_state(d, uid, f"newcat_emoji|{text}")
        await update.message.reply_text(
            f"Name: <b>{esc(text)}</b>\n\nNow send the emoji for this category:",
            parse_mode="HTML")
        return

    if state and state.startswith("newcat_emoji|") and is_admin(uid, d):
        cat_name = state[len("newcat_emoji|"):]
        emoji    = text.strip()
        if not emoji:
            await update.message.reply_text("Please send a valid emoji."); return
        cat_key = "custom_" + re.sub(r'[^a-z0-9]', '_', cat_name.lower())[:20] + "_" + uuid.uuid4().hex[:4]
        d.setdefault("custom_cats", []).append({
            "key": cat_key, "label": cat_name, "emoji": emoji, "products": []
        })
        save(d); merge_custom_cats(d)
        set_state(d, uid, f"newcat_products|{cat_key}")
        await update.message.reply_text(
            f"Category <b>{esc(cat_name)}</b> created!\n\n"
            f"Add products one by one:\n"
            f"<code>Product Name | 31 Days 23.00 | 7 Days 15.00 | 1 Day 5.00</code>\n\n"
            f"Send <b>DONE</b> when finished.", parse_mode="HTML")
        return

    if state and state.startswith("newcat_products|") and is_admin(uid, d):
        cat_key = state[len("newcat_products|"):]
        if text.upper() == "DONE":
            cat_data = next((c for c in d.get("custom_cats", []) if c["key"] == cat_key), None)
            clear_state(d, uid)
            if cat_data:
                await update.message.reply_text(
                    f"Category saved!\n<b>{esc(cat_data['label'])}</b>\n"
                    f"Products: <b>{len(cat_data.get('products',[]))}</b>",
                    parse_mode="HTML", reply_markup=kb_main(uid, d))
            else:
                await update.message.reply_text("Done.", reply_markup=kb_main(uid, d))
            return
        parsed = parse_product_line(text)
        if not parsed:
            await update.message.reply_text(
                "Invalid format. Use:\n<code>Name | 31 Days 23.00 | 7 Days 15.00</code>\n"
                "Or send <b>DONE</b> to finish.", parse_mode="HTML")
            return
        prod_name, prices = parsed
        cat_data = next((c for c in d.get("custom_cats", []) if c["key"] == cat_key), None)
        if not cat_data:
            clear_state(d, uid); return
        cat_data["products"].append({"name": prod_name, "prices": prices})
        save(d); merge_custom_cats(d)
        price_lines = "\n".join(f"   - {dur}  -  ${p}" for dur, p in prices)
        await update.message.reply_text(
            f"Added: {esc(prod_name)}\n{price_lines}\n\nSend more or <b>DONE</b>.",
            parse_mode="HTML")
        return

    if state and state.startswith("add_file_item|") and is_admin(uid, d):
        parts = state.split("|", 3)
        if len(parts) != 3:
            await update.message.reply_text("Error. Use /start."); return
        _, cat, idx_str = parts; idx = int(idx_str)
        file_item = {"type": "link", "value": text, "name": text[:60]}
        set_file_data(cat, idx, file_item, d)
        clear_state(d, uid)
        prod_name = MENU[cat]["products"][idx]["name"] if idx < len(MENU[cat]["products"]) else f"#{idx}"
        await update.message.reply_text(
            f"Link Set!\nProduct: <b>{esc(prod_name)}</b>\nLink: <code>{esc(text[:80])}</code>",
            parse_mode="HTML")
        return

    if state and state.startswith("add_keys_item|") and is_admin(uid, d):
        parts = state.split("|", 3)
        if len(parts) != 4:
            await update.message.reply_text("Error. Use /start."); return
        _, cat, idx_str, dur = parts; idx = int(idx_str)
        new_keys = [l.strip() for l in text.strip().splitlines() if l.strip()]
        if not new_keys:
            await update.message.reply_text("No keys found. Send at least one key."); return
        slot = key_slot(cat, idx, dur)
        d.setdefault("keys", {}).setdefault(slot, []).extend(new_keys)
        clear_state(d, uid); save(d)
        prod_name = MENU[cat]["products"][idx]["name"] if idx < len(MENU[cat]["products"]) else f"#{idx}"
        await update.message.reply_text(
            f"<b>Keys Added!</b>\n\nProduct: <b>{esc(prod_name)}</b>\n"
            f"Duration: <b>{esc(dur)}</b>\nAdded: <b>{len(new_keys)}</b> keys\n"
            f"Total: <b>{len(d['keys'][slot])}</b>", parse_mode="HTML")
        return

    if state and state.startswith("edit_price_val|") and is_admin(uid, d):
        parts = state.split("|", 4)
        if len(parts) != 4:
            await update.message.reply_text("Error. Use /start."); return
        _, cat, idx_str, dur_enc = parts
        idx = int(idx_str)
        dur = dur_enc.replace("~", " ")
        try:
            new_price = float(text.strip())
            if new_price < 0: raise ValueError
        except ValueError:
            await update.message.reply_text("Invalid price. Send a number like: 12.50"); return
        override_key = f"{cat}_{idx}_{dur}"
        d.setdefault("price_overrides", {})[override_key] = f"{new_price:.2f}"
        save(d); clear_state(d, uid)
        prod_name = MENU[cat]["products"][idx]["name"] if idx < len(MENU.get(cat, {}).get("products", [])) else f"#{idx}"
        await update.message.reply_text(
            f"<b>Price Updated!</b>\n\nProduct: <b>{esc(prod_name)}</b>\n"
            f"Duration: <b>{esc(dur)}</b>\nNew price: <b>${new_price:.2f}</b>",
            parse_mode="HTML", reply_markup=kb_admin())
        return

    # Edit reseller price — receive new price
    if state and state.startswith("edit_reseller_price_val|") and is_admin(uid, d):
        parts = state.split("|", 4)
        if len(parts) != 4:
            await update.message.reply_text("Error. Use /start."); return
        _, cat, idx_str, dur_enc = parts
        idx = int(idx_str)
        dur = dur_enc.replace("~", " ")
        if text.strip().upper() == "REMOVE":
            rkey = reseller_price_key(cat, idx, dur)
            d.setdefault("reseller_prices", {}).pop(rkey, None)
            save(d); clear_state(d, uid)
            await update.message.reply_text("Reseller price removed.", reply_markup=kb_admin())
            return
        try:
            new_price = float(text.strip())
            if new_price < 0: raise ValueError
        except ValueError:
            await update.message.reply_text("Invalid price. Send a number like: 12.50\nOr send REMOVE to remove the reseller price."); return
        rkey = reseller_price_key(cat, idx, dur)
        d.setdefault("reseller_prices", {})[rkey] = f"{new_price:.2f}"
        save(d); clear_state(d, uid)
        prod_name = MENU[cat]["products"][idx]["name"] if idx < len(MENU.get(cat, {}).get("products", [])) else f"#{idx}"
        await update.message.reply_text(
            f"<b>Reseller Price Updated!</b>\n\nProduct: <b>{esc(prod_name)}</b>\n"
            f"Duration: <b>{esc(dur)}</b>\nReseller price: <b>${new_price:.2f}</b>",
            parse_mode="HTML", reply_markup=kb_admin())
        return

    if state == "add_reseller" and is_admin(uid, d):
        try:
            tid = int(text.strip())
        except ValueError:
            await update.message.reply_text("Invalid. Send a numeric Telegram user ID."); return
        d.setdefault("resellers", {})[str(tid)] = {}
        if tid not in d.get("verified", []):
            d.setdefault("verified", []).append(tid)
        save(d); clear_state(d, uid)
        await update.message.reply_text(
            f"<b>Reseller Added!</b>\n\nUser: <code>{tid}</code>\n\n"
            f"Use <b>Edit Reseller Prices</b> to set their custom prices.",
            parse_mode="HTML", reply_markup=kb_admin())
        return

    if state == "admin_id" and is_admin(uid, d):
        try: new_admin = int(text.strip())
        except ValueError:
            await update.message.reply_text("Invalid user ID."); return
        if new_admin not in d.get("admin_ids", []):
            d.setdefault("admin_ids", []).append(new_admin)
        if new_admin not in d.get("verified", []):
            d.setdefault("verified", []).append(new_admin)
        save(d); clear_state(d, uid)
        await update.message.reply_text(f"Admin added: <code>{new_admin}</code>", parse_mode="HTML")
        return

    if state == "add_bal" and is_admin(uid, d):
        parts = text.split()
        if len(parts) != 2:
            await update.message.reply_text("Send: USER_ID AMOUNT"); return
        try: tid = int(parts[0]); amt = float(parts[1])
        except ValueError:
            await update.message.reply_text("Invalid."); return
        cur = get_balance(tid, d)
        d["balances"][str(tid)] = round(cur + amt, 2)
        save(d)
        add_balance_tx(tid, amt, "Added by admin", load())
        clear_state(d, uid)
        await update.message.reply_text(
            f"Added <b>${amt:.2f}</b> to <code>{tid}</code>. Balance: <b>${cur+amt:.2f}</b>",
            parse_mode="HTML", reply_markup=kb_admin())
        return

    if state == "ded_bal" and is_admin(uid, d):
        parts = text.split()
        if len(parts) != 2:
            await update.message.reply_text("Send: USER_ID AMOUNT"); return
        try: tid = int(parts[0]); amt = float(parts[1])
        except ValueError:
            await update.message.reply_text("Invalid."); return
        cur = get_balance(tid, d)
        new = max(0.0, cur - amt)
        d["balances"][str(tid)] = round(new, 2)
        save(d)
        add_balance_tx(tid, -amt, "Deducted by admin", load())
        clear_state(d, uid)
        await update.message.reply_text(
            f"Deducted <b>${amt:.2f}</b> from <code>{tid}</code>. Balance: <b>${new:.2f}</b>",
            parse_mode="HTML", reply_markup=kb_admin())
        return

    if state == "chk_bal" and is_admin(uid, d):
        try: tid = int(text.strip())
        except ValueError:
            await update.message.reply_text("Invalid user ID."); return
        bal = get_balance(tid, d)
        clear_state(d, uid)
        await update.message.reply_text(
            f"User <code>{tid}</code> balance: <b>${bal:.2f}</b>", parse_mode="HTML")
        return

    if state == "broadcast" and is_admin(uid, d):
        all_uids = list(set(d.get("verified", []) + OWNER_IDS + d.get("admin_ids", [])))
        sent = 0
        for target_uid in all_uids:
            try:
                await ctx.bot.send_message(chat_id=target_uid, text=text)
                sent += 1
                await asyncio.sleep(0.05)
            except Exception: pass
        clear_state(d, uid)
        await update.message.reply_text(f"Broadcast sent to {sent} users.", reply_markup=kb_admin())
        return

    if state == "set_bnb_id" and is_admin(uid, d):
        d["settings"]["binance_id"] = text.strip()
        save(d); clear_state(d, uid)
        await update.message.reply_text(f"Binance ID set: <code>{esc(text.strip())}</code>",
            parse_mode="HTML", reply_markup=kb_admin())
        return

    if state == "set_support" and is_admin(uid, d):
        d["settings"]["support"] = text.strip()
        save(d); clear_state(d, uid)
        await update.message.reply_text(f"Support contact set: {esc(text.strip())}", reply_markup=kb_admin())
        return

    if state == "set_shop_name" and is_admin(uid, d):
        d["settings"]["shop_name"] = text.strip()
        save(d); clear_state(d, uid)
        await update.message.reply_text(f"Shop name set: <b>{esc(text.strip())}</b>",
            parse_mode="HTML", reply_markup=kb_admin())
        return

    if state == "ban_user" and is_admin(uid, d):
        try:
            target_uid = int(text.strip())
        except ValueError:
            await update.message.reply_text("Invalid ID. Send a numeric Telegram user ID.", reply_markup=kb_admin())
            return
        if target_uid in OWNER_IDS:
            await update.message.reply_text("Cannot ban an owner.", reply_markup=kb_admin())
            return
        banned = d.setdefault("banned_users", [])
        if target_uid not in banned:
            banned.append(target_uid)
            save(d)
        clear_state(d, uid)
        await update.message.reply_text(
            f"{CE_BAN} <b>User banned:</b> <code>{target_uid}</code>",
            parse_mode="HTML", reply_markup=kb_admin())
        try:
            await ctx.bot.send_message(chat_id=target_uid,
                text=f"{CE_BAN} <b>You have been banned from this bot.</b>\n\nContact support: {esc(support_contact(d))}",
                parse_mode="HTML")
        except Exception: pass
        return

    if state == "unban_user" and is_admin(uid, d):
        try:
            target_uid = int(text.strip())
        except ValueError:
            await update.message.reply_text("Invalid ID. Send a numeric Telegram user ID.", reply_markup=kb_admin())
            return
        banned = d.get("banned_users", [])
        if target_uid in banned:
            banned.remove(target_uid)
            save(d)
            msg_text = f"<b>User unbanned:</b> <code>{target_uid}</code>"
        else:
            msg_text = f"User <code>{target_uid}</code> is not banned."
        clear_state(d, uid)
        await update.message.reply_text(msg_text, parse_mode="HTML", reply_markup=kb_admin())
        return

# ═══════════════════════════════════════════════════════════════════
#  CALLBACK HANDLER
# ═══════════════════════════════════════════════════════════════════
async def handle_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q   = update.callback_query
    uid = q.from_user.id
    cb  = q.data
    await q.answer()
    d = load()

    if cb == "support_cancel":
        clear_state(d, uid)
        try: await q.edit_message_text("Cancelled.")
        except Exception: pass
        return

    if cb == "acc|history":
        hist = get_purchase_history(uid, d)
        if not hist:
            await q.message.reply_text("No purchase history yet."); return
        uname = q.from_user.username
        uname_str = f"@{esc(uname)}" if uname else f"ID: <code>{uid}</code>"
        lines = [f"<b>Purchase History</b>\nUser: {uname_str}\n"]
        for i, entry in enumerate(reversed(hist), 1):
            entry_user = entry.get("username", "")
            user_line  = f"@{esc(entry_user)}" if entry_user else uname_str
            lines.append(
                f"<b>#{i}</b> {esc(entry['product'])}\n"
                f"   {esc(entry['duration'])}  |  ${esc(entry['price'])}\n"
                f"   {esc(entry['method'])}  |  {esc(entry['date'])}\n"
                f"   {user_line}\n")
            if i >= 20:
                lines.append(f"<i>...and {len(hist)-20} more</i>"); break
        try: await q.message.reply_text("\n".join(lines)[:4096], parse_mode="HTML")
        except Exception: await q.message.reply_text("Could not load history.")
        return

    if cb == "acc|bal_history":
        hist = get_balance_tx_history(uid, d)
        if not hist:
            await q.answer("No balance history yet.", show_alert=True); return
        uname = q.from_user.username
        uname_str = f"@{esc(uname)}" if uname else f"ID: <code>{uid}</code>"
        lines = [f"{CE_PRICE} <b>Balance History</b>\nUser: {uname_str}\n"]
        for entry in reversed(hist[-30:]):
            amt    = entry["amount"]
            sign   = "+" if amt >= 0 else ""
            lines.append(
                f"<b>{sign}${amt:.2f}</b>  —  {esc(entry['note'])}\n"
                f"<i>{esc(entry['date'])}</i>\n")
        try: await q.message.reply_text("\n".join(lines)[:4096], parse_mode="HTML")
        except Exception: pass
        return

    if cb == "verify":
        is_new = uid not in d.get("verified", [])
        msg, ok = await run_verify(q, uid, ctx)
        if ok:
            track_user(uid, q.from_user, d)
            d2 = load()
            if uid not in d2.get("verified", []):
                d2.setdefault("verified", []).append(uid)
                save(d2)
            name = esc(q.from_user.first_name or "there")
            uname_str = f"@{q.from_user.username}" if q.from_user.username else f"ID: {uid}"
            if is_new:
                d3 = load()
                total_users = len(d3.get("all_users", {}))
                all_admins = list(set(OWNER_IDS + d3.get("admin_ids", [])))
                for aid in all_admins:
                    try:
                        await ctx.bot.send_message(chat_id=aid,
                            text=(f"{CE_NEWUSER} <b>New User Verified!</b>\n\n"
                                  f"Name: <b>{name}</b>\n"
                                  f"Username: {esc(uname_str)}\n"
                                  f"ID: <code>{uid}</code>\n\n"
                                  f"Total users: <b>{total_users}</b>"),
                            parse_mode="HTML")
                    except Exception: pass
            d4 = load()
            await q.message.reply_text(
                f"{CE_WELCOME} <b>Welcome, {name}!</b>\n\nYou now have full access to the shop.",
                parse_mode="HTML", reply_markup=kb_main(uid, d4))
        return

    if not is_verified(uid, d):
        await q.answer("Please verify first. Use /start", show_alert=True); return

    # ── Approve/Deny ────────────────────────────────────────────────
    if cb.startswith("approve|"):
        if not is_admin(uid, d):
            await q.answer("Admins only.", show_alert=True); return
        order_id = cb[8:]
        order    = d.get("pending_orders", {}).get(order_id)
        if not order:
            await q.answer("Order not found or already processed.", show_alert=True)
            try: await q.edit_message_reply_markup(reply_markup=None)
            except Exception: pass
            return
        user_id = order["user_id"]
        success = await deliver_product(user_id, order, ctx)
        d2 = load(); d2.get("pending_orders", {}).pop(order_id, None); save(d2)
        if success:
            await q.answer("Approved! Product delivered.", show_alert=False)
            try:
                await q.edit_message_caption(
                    caption=(q.message.caption or "") + "\n\nAPPROVED",
                    parse_mode="HTML", reply_markup=None)
            except Exception: pass
        else:
            await q.answer("No stock available!", show_alert=True)
            try:
                await q.edit_message_caption(
                    caption=(q.message.caption or "") + "\n\nAPPROVED but NO STOCK",
                    parse_mode="HTML", reply_markup=None)
            except Exception: pass
            try:
                await ctx.bot.send_message(chat_id=user_id,
                    text=f"<b>Payment approved but product is out of stock.</b>\n\n"
                         f"Please contact admin: {esc(support_contact(d2))}", parse_mode="HTML")
            except Exception: pass
        return

    if cb.startswith("deny|"):
        if not is_admin(uid, d):
            await q.answer("Admins only.", show_alert=True); return
        order_id = cb[5:]
        order    = d.get("pending_orders", {}).get(order_id)
        if not order:
            await q.answer("Order not found or already processed.", show_alert=True)
            try: await q.edit_message_reply_markup(reply_markup=None)
            except Exception: pass
            return
        user_id = order["user_id"]
        d.get("pending_orders", {}).pop(order_id, None); save(d)
        await q.answer("Denied.", show_alert=False)
        try:
            await q.edit_message_caption(
                caption=(q.message.caption or "") + "\n\nDENIED",
                parse_mode="HTML", reply_markup=None)
        except Exception: pass
        try:
            await ctx.bot.send_message(chat_id=user_id,
                text=f"<b>Payment Denied</b>\n\nContact admin: {esc(support_contact(d))}",
                parse_mode="HTML")
        except Exception: pass
        return

    # ── Delete custom category ──────────────────────────────────────
    if cb.startswith("del_cat|"):
        if not is_admin(uid, d):
            await q.answer("Admins only.", show_alert=True); return
        cat_key  = cb[8:]
        cat_data = next((c for c in d.get("custom_cats", []) if c["key"] == cat_key), None)
        if not cat_data:
            await q.answer("Category not found.", show_alert=True); return
        await q.edit_message_text(
            f"<b>Delete Category</b>\n\n<b>{esc(cat_data['label'])}</b>\n\n"
            f"This removes the category and all its keys/files. Sure?",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Yes, Delete", callback_data=f"del_cat_confirm|{cat_key}")],
                [InlineKeyboardButton("Cancel",      callback_data="adm|cancel")],
            ]))
        return

    if cb.startswith("del_cat_confirm|"):
        if not is_admin(uid, d):
            await q.answer("Admins only.", show_alert=True); return
        cat_key  = cb[len("del_cat_confirm|"):]
        cat_data = MENU.get(cat_key, {})
        for i in range(len(cat_data.get("products", []))):
            for dur, _ in cat_data["products"][i].get("prices", []):
                d.get("keys", {}).pop(key_slot(cat_key, i, dur), None)
            d.get("files", {}).pop(file_slot(cat_key, i), None)
        d["custom_cats"] = [c for c in d.get("custom_cats", []) if c["key"] != cat_key]
        save(d); merge_custom_cats(d)
        await q.edit_message_text("Category deleted.")
        return

    if cb.startswith("rem_res_confirm|"):
        if not is_admin(uid, d):
            await q.answer("Admins only.", show_alert=True); return
        tid_str = cb[len("rem_res_confirm|"):]
        d.get("resellers", {}).pop(tid_str, None); save(d)
        await q.edit_message_text(f"Reseller <code>{tid_str}</code> removed.", parse_mode="HTML")
        return

    # ── Shop flow ───────────────────────────────────────────────────
    if cb.startswith("cats|"):
        mode = cb[5:]
        reseller_mode = (mode == "r") and is_reseller(uid, d)
        label = f"{CE_SELECT} <b>Reseller Shop - Select a category:</b>" if reseller_mode else f"{CE_SELECT} <b>Select a category:</b>"
        try: await q.edit_message_text(label,
                parse_mode="HTML", reply_markup=kb_cats(uid, d, reseller_mode=reseller_mode))
        except Exception:
            await q.message.reply_text(label,
                parse_mode="HTML", reply_markup=kb_cats(uid, d, reseller_mode=reseller_mode))
        return

    if cb.startswith("cat|"):
        parts = cb.split("|", 2)
        k    = parts[1]
        mode = parts[2] if len(parts) > 2 else "u"
        cat  = MENU.get(k)
        if not cat: return
        reseller_mode = (mode == "r") and is_reseller(uid, d)
        text_msg = cat_msg(k, uid, d, reseller_mode=reseller_mode)
        oos = cat_is_oos(k, d)
        kb  = (InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data=f"cats|{mode}")]]) 
               if oos else kb_cat(k, reseller_mode=reseller_mode))
        try: await q.edit_message_text(text_msg, parse_mode="HTML", reply_markup=kb)
        except Exception: await q.message.reply_text(text_msg, parse_mode="HTML", reply_markup=kb)
        return

    if cb.startswith("prod|"):
        parts = cb.split("|")
        k = parts[1]; i = int(parts[2]); mode = parts[3] if len(parts) > 3 else "u"
        cat = MENU.get(k)
        if not cat or i >= len(cat.get("products", [])): return
        p     = cat["products"][i]
        total = total_product_stock(k, i, d)
        reseller_mode = (mode == "r") and is_reseller(uid, d)
        res_note = "\n<i>Reseller price applied</i>" if reseller_mode else ""
        txt = (f"<b>{esc(p['name'])}</b>\n\n"
               f"Status: Good and Safe\n"
               f"In stock: <b>{total}</b>{res_note}\n\n<b>Select a duration:</b>")
        try: await q.edit_message_text(txt, parse_mode="HTML", reply_markup=kb_durations(k, i, uid, d, reseller_mode))
        except Exception: await q.message.reply_text(txt, parse_mode="HTML", reply_markup=kb_durations(k, i, uid, d, reseller_mode))
        return

    if cb.startswith("prod_back|"):
        parts = cb.split("|")
        k = parts[1]; mode = parts[2] if len(parts) > 2 else "u"
        cat = MENU.get(k)
        if not cat: return
        reseller_mode = (mode == "r") and is_reseller(uid, d)
        text_msg = cat_msg(k, uid, d, reseller_mode=reseller_mode)
        try: await q.edit_message_text(text_msg, parse_mode="HTML", reply_markup=kb_cat(k, reseller_mode=reseller_mode))
        except Exception: await q.message.reply_text(text_msg, parse_mode="HTML", reply_markup=kb_cat(k, reseller_mode=reseller_mode))
        return

    if cb.startswith("dur|"):
        parts = cb.split("|", 6)
        _, k, si, dur, price = parts[0], parts[1], parts[2], parts[3], parts[4]
        mode = parts[5] if len(parts) > 5 else "u"
        i = int(si)
        cat = MENU.get(k)
        if not cat or i >= len(cat.get("products", [])): return
        p   = cat["products"][i]
        qty = slot_stock(k, i, dur, d)
        bal = get_balance(uid, d)
        reseller_mode = (mode == "r") and is_reseller(uid, d)
        res_note = "  [RESELLER PRICE]" if reseller_mode else ""
        txt = (f"<b>{esc(p['name'])}</b>\n"
               f"Duration: <b>{esc(dur)}</b>  |  Price: <b>${esc(price)}</b>{res_note}\n"
               f"In stock: <b>{qty}</b>\n"
               f"Your balance: <b>${bal:.2f}</b>\n\n<b>Choose payment method:</b>")
        if qty == 0:
            await q.answer("This duration is out of stock!", show_alert=True); return
        try: await q.edit_message_text(txt, parse_mode="HTML",
                reply_markup=kb_payment(k, i, dur, price, uid, d, mode))
        except Exception: await q.message.reply_text(txt, parse_mode="HTML",
                reply_markup=kb_payment(k, i, dur, price, uid, d, mode))
        return

    if cb.startswith("pay|"):
        parts  = cb.split("|", 7)
        method = parts[1]
        k, si, dur, price = parts[2], parts[3], parts[4], parts[5]
        mode = parts[6] if len(parts) > 6 else "u"
        i = int(si)
        cat = MENU.get(k)
        if not cat or i >= len(cat.get("products", [])): return
        p = cat["products"][i]

        if method == "bal":
            try: price_f = float(price)
            except ValueError:
                await q.answer("Invalid price.", show_alert=True); return
            bal = get_balance(uid, d)
            if bal < price_f:
                await q.answer(f"Insufficient balance. You have ${bal:.2f}", show_alert=True); return
            if slot_stock(k, i, dur, d) == 0:
                await q.answer("No stock! Contact admin.", show_alert=True); return
            d["balances"][str(uid)] = round(bal - price_f, 2); save(d)
            add_balance_tx(uid, -price_f, f"Purchase: {MENU[k]['products'][i]['name']} ({dur})", load())
            order   = {"k": k, "i": i, "dur": dur, "price": price, "method": "bal", "username": q.from_user.username or ""}
            success = await deliver_product(uid, order, ctx)
            if success:
                try:
                    await q.edit_message_text(
                        f"<b>Payment Successful!</b>\n\n"
                        f"${price_f:.2f} deducted.\nRemaining: <b>${d['balances'][str(uid)]:.2f}</b>\n\nKey sent!",
                        parse_mode="HTML")
                except Exception: pass
            else:
                d2 = load()
                d2["balances"][str(uid)] = round(get_balance(uid, d2) + price_f, 2); save(d2)
                add_balance_tx(uid, price_f, "Refund: out of stock", load())
                await q.answer("Out of stock! Balance refunded.", show_alert=True)
            return

        await send_payment_details(q.message, k, i, dur, price, method, d, ctx, mode)
        return

    if cb.startswith("paid|"):
        parts  = cb.split("|", 7)
        k, si, dur, price, method = parts[1], parts[2], parts[3], parts[4], parts[5]
        mode = parts[6] if len(parts) > 6 else "u"
        i = int(si)
        cat = MENU.get(k)
        if not cat or i >= len(cat.get("products", [])): return
        p = cat["products"][i]
        if slot_stock(k, i, dur, d) == 0:
            await q.answer("No stock! Contact admin.", show_alert=True)
            all_admins = list(set(OWNER_IDS + d.get("admin_ids", [])))
            for aid in all_admins:
                try:
                    await ctx.bot.send_message(chat_id=aid,
                        text=f"<b>Out of Stock Alert</b>\n\nUser: <code>{uid}</code>\n"
                             f"Product: {esc(p['name'])}\nDuration: {esc(dur)}\nPlease restock!",
                        parse_mode="HTML")
                except Exception: pass
            return
        set_state(d, uid, f"waiting_ss|{k}|{i}|{dur}|{price}|{method}|{mode}")
        await q.message.reply_text(
            "<b>Send Payment Screenshot</b>\n\n"
            "Please send a photo of your payment receipt.\n"
            "An admin will review and approve your order.", parse_mode="HTML")
        return

    # ── Admin: Add Files ────────────────────────────────────────────
    if cb.startswith("afc|"):
        if not is_admin(uid, d): await q.answer("Admins only.", show_alert=True); return
        cat_key = cb[4:]
        cat     = MENU.get(cat_key)
        if not cat: return
        await q.edit_message_text(
            f"<b>Add/Replace File - {esc(cat['label'])}</b>\n\nSelect a product:",
            parse_mode="HTML", reply_markup=kb_adm_prods_files("f", cat_key))
        return

    if cb.startswith("afp|"):
        if not is_admin(uid, d): await q.answer("Admins only.", show_alert=True); return
        _, cat_key, idx_str = cb.split("|", 2); idx = int(idx_str)
        cat = MENU.get(cat_key)
        if not cat or idx >= len(cat.get("products", [])): return
        prod     = cat["products"][idx]
        existing = get_file(cat_key, idx, d)
        existing_info = f"\nCurrent: <b>{esc(existing.get('name','?'))}</b>" if existing else "\nNo file set yet."
        set_state(d, uid, f"add_file_item|{cat_key}|{idx}")
        await q.edit_message_text(
            f"<b>Add/Replace File - {esc(prod['name'])}</b>\n{existing_info}\n\n"
            f"Send the file:\n- IPA/APK/ZIP as document\n"
            f"- Download link as text\n\n<i>Replaces existing file.</i>",
            parse_mode="HTML")
        return

    if cb.startswith("arc|"):
        if not is_admin(uid, d): await q.answer("Admins only.", show_alert=True); return
        cat_key = cb[4:]
        cat     = MENU.get(cat_key)
        if not cat: return
        await q.edit_message_text(
            f"<b>Remove File - {esc(cat['label'])}</b>\n\nSelect a product:",
            parse_mode="HTML", reply_markup=kb_adm_prods_files("r", cat_key))
        return

    if cb.startswith("arp|"):
        if not is_admin(uid, d): await q.answer("Admins only.", show_alert=True); return
        _, cat_key, idx_str = cb.split("|", 2); idx = int(idx_str)
        cat = MENU.get(cat_key)
        if not cat or idx >= len(cat.get("products", [])): return
        prod     = cat["products"][idx]
        existing = get_file(cat_key, idx, d)
        if not existing:
            await q.edit_message_text(
                f"<b>{esc(prod['name'])}</b> has no file set.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Back", callback_data="adm|remove_file")
                ]]))
            return
        file_desc = f"\nCurrent: <code>{esc(existing.get('name','?'))}</code> [{existing.get('type','?')}]"
        await q.edit_message_text(
            f"<b>Remove File - {esc(prod['name'])}</b>\n{file_desc}\n\nConfirm removal?",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Yes, Remove", callback_data=f"arc_confirm|{cat_key}|{idx}")],
                [InlineKeyboardButton("Back",        callback_data="adm|remove_file")],
            ]))
        return

    if cb.startswith("arc_confirm|"):
        if not is_admin(uid, d): await q.answer("Admins only.", show_alert=True); return
        _, cat_key, idx_str = cb.split("|", 2); idx = int(idx_str)
        existing = get_file(cat_key, idx, d)
        if existing:
            remove_file_data(cat_key, idx, d)
            await q.edit_message_text(
                f"File removed: <code>{esc(existing.get('name','?'))}</code>", parse_mode="HTML")
        else:
            await q.edit_message_text("No file to remove.")
        return

    # ── Admin: Add Keys ─────────────────────────────────────────────
    if cb.startswith("akc|"):
        if not is_admin(uid, d): await q.answer("Admins only.", show_alert=True); return
        cat_key = cb[4:]
        cat     = MENU.get(cat_key)
        if not cat: return
        await q.edit_message_text(
            f"<b>Add Keys - {esc(cat['label'])}</b>\n\nSelect a product:",
            parse_mode="HTML", reply_markup=kb_adm_prods_keys(cat_key))
        return

    if cb.startswith("akp|"):
        if not is_admin(uid, d): await q.answer("Admins only.", show_alert=True); return
        _, cat_key, idx_str = cb.split("|", 2); idx = int(idx_str)
        cat = MENU.get(cat_key)
        if not cat or idx >= len(cat.get("products", [])): return
        prod = cat["products"][idx]
        await q.edit_message_text(
            f"<b>Add Keys - {esc(prod['name'])}</b>\n\nSelect a duration:",
            parse_mode="HTML", reply_markup=kb_adm_durs_keys(cat_key, idx))
        return

    if cb.startswith("akd|"):
        if not is_admin(uid, d): await q.answer("Admins only.", show_alert=True); return
        parts   = cb.split("|")
        cat_key, idx_str, dur_enc = parts[1], parts[2], parts[3]
        idx = int(idx_str); dur = dur_enc.replace("~", " ")
        cat = MENU.get(cat_key)
        if not cat or idx >= len(cat.get("products", [])): return
        prod     = cat["products"][idx]
        existing = keys_count(cat_key, idx, dur, d)
        set_state(d, uid, f"add_keys_item|{cat_key}|{idx}|{dur}")
        await q.edit_message_text(
            f"<b>Add Keys</b>\n\nProduct: <b>{esc(prod['name'])}</b>\n"
            f"Duration: <b>{esc(dur)}</b>\nCurrent stock: <b>{existing}</b>\n\n"
            f"Send your keys - <b>one per line</b>:", parse_mode="HTML")
        return

    # ── Admin: Edit Regular Price ────────────────────────────────────
    if cb.startswith("epc|"):
        if not is_admin(uid, d): await q.answer("Admins only.", show_alert=True); return
        cat_key = cb[4:]
        cat     = MENU.get(cat_key)
        if not cat: return
        await q.edit_message_text(
            f"<b>Edit Price - {esc(cat['label'])}</b>\n\nSelect a product:",
            parse_mode="HTML", reply_markup=kb_adm_prods_price(cat_key))
        return

    if cb.startswith("epp|"):
        if not is_admin(uid, d): await q.answer("Admins only.", show_alert=True); return
        _, cat_key, idx_str = cb.split("|", 2); idx = int(idx_str)
        cat = MENU.get(cat_key)
        if not cat or idx >= len(cat.get("products", [])): return
        prod = cat["products"][idx]
        await q.edit_message_text(
            f"<b>Edit Price - {esc(prod['name'])}</b>\n\nSelect a duration to edit:",
            parse_mode="HTML", reply_markup=kb_adm_durs_price(cat_key, idx, d))
        return

    if cb.startswith("epd|"):
        if not is_admin(uid, d): await q.answer("Admins only.", show_alert=True); return
        parts = cb.split("|"); cat_key, idx_str, dur_enc = parts[1], parts[2], parts[3]
        idx = int(idx_str); dur = dur_enc.replace("~", " ")
        cat = MENU.get(cat_key)
        if not cat or idx >= len(cat.get("products", [])): return
        prod      = cat["products"][idx]
        cur_price = get_base_price(cat_key, idx, dur, d)
        set_state(d, uid, f"edit_price_val|{cat_key}|{idx}|{dur_enc}")
        await q.edit_message_text(
            f"<b>Edit Price</b>\n\nProduct: <b>{esc(prod['name'])}</b>\n"
            f"Duration: <b>{esc(dur)}</b>\nCurrent price: <b>${cur_price}</b>\n\n"
            f"Send the new price (e.g. <code>12.50</code>):",
            parse_mode="HTML")
        return

    # ── Admin: Edit Reseller Price ───────────────────────────────────
    if cb.startswith("erpc|"):
        if not is_admin(uid, d): await q.answer("Admins only.", show_alert=True); return
        cat_key = cb[5:]
        cat     = MENU.get(cat_key)
        if not cat: return
        await q.edit_message_text(
            f"<b>Edit Reseller Price - {esc(cat['label'])}</b>\n\nSelect a product:",
            parse_mode="HTML", reply_markup=kb_adm_prods_reseller_price(cat_key))
        return

    if cb.startswith("erpp|"):
        if not is_admin(uid, d): await q.answer("Admins only.", show_alert=True); return
        _, cat_key, idx_str = cb.split("|", 2); idx = int(idx_str)
        cat = MENU.get(cat_key)
        if not cat or idx >= len(cat.get("products", [])): return
        prod = cat["products"][idx]
        await q.edit_message_text(
            f"<b>Edit Reseller Price - {esc(prod['name'])}</b>\n\nSelect a duration:",
            parse_mode="HTML", reply_markup=kb_adm_durs_reseller_price(cat_key, idx, d))
        return

    if cb.startswith("erpd|"):
        if not is_admin(uid, d): await q.answer("Admins only.", show_alert=True); return
        parts = cb.split("|"); cat_key, idx_str, dur_enc = parts[1], parts[2], parts[3]
        idx = int(idx_str); dur = dur_enc.replace("~", " ")
        cat = MENU.get(cat_key)
        if not cat or idx >= len(cat.get("products", [])): return
        prod      = cat["products"][idx]
        base_price = get_base_price(cat_key, idx, dur, d)
        cur_rp    = get_reseller_price(cat_key, idx, dur, d)
        cur_display = f"${cur_rp}" if cur_rp else "not set (uses base price)"
        set_state(d, uid, f"edit_reseller_price_val|{cat_key}|{idx}|{dur_enc}")
        await q.edit_message_text(
            f"<b>Edit Reseller Price</b>\n\nProduct: <b>{esc(prod['name'])}</b>\n"
            f"Duration: <b>{esc(dur)}</b>\nBase price: <b>${base_price}</b>\n"
            f"Current reseller price: <b>{cur_display}</b>\n\n"
            f"Send the new reseller price (e.g. <code>8.50</code>)\n"
            f"Or send <b>REMOVE</b> to remove custom price:",
            parse_mode="HTML")
        return

    # ── Admin panel actions ─────────────────────────────────────────
    if cb.startswith("adm|"):
        if not is_admin(uid, d):
            await q.answer("Admins only.", show_alert=True); return
        action = cb[4:]

        if action == "noop":
            return

        if action == "add_keys":
            clear_state(d, uid)
            await q.message.reply_text("<b>Add Keys</b>\n\nSelect a category:",
                parse_mode="HTML", reply_markup=kb_adm_cats_keys())

        elif action == "add_files":
            clear_state(d, uid)
            await q.message.reply_text("<b>Add/Replace File</b>\n\nSelect a category:",
                parse_mode="HTML", reply_markup=kb_adm_cats_files("f"))

        elif action == "remove_file":
            clear_state(d, uid)
            await q.message.reply_text("<b>Remove File</b>\n\nSelect a category:",
                parse_mode="HTML", reply_markup=kb_adm_cats_files("r"))

        elif action == "add_cat":
            clear_state(d, uid)
            set_state(d, uid, "newcat_name")
            await q.message.reply_text(
                "<b>Add New Category</b>\n\nStep 1 - Send the category name:",
                parse_mode="HTML")

        elif action == "del_cat":
            custom = d.get("custom_cats", [])
            if not custom:
                await q.answer("No custom categories to delete.", show_alert=True); return
            await q.message.reply_text(
                "<b>Delete Category</b>\n\nSelect a custom category to delete:",
                parse_mode="HTML", reply_markup=kb_del_custom_cats(d))

        elif action == "view_keys":
            all_lines = ["<b>Keys Stock</b>\n"]
            for k in CAT_ORDER:
                cat = MENU.get(k, {})
                if not cat.get("products"): continue
                all_lines.append(f"<b>{esc(cat['label'])}</b>")
                for i, p in enumerate(cat["products"]):
                    for dur, _ in p["prices"]:
                        kqty = keys_count(k, i, dur, d)
                        dot  = "[+]" if kqty > 0 else "[-]"
                        all_lines.append(f"  {dot} {esc(p['name'])} - {esc(dur)}: <b>{kqty}</b>")
                all_lines.append("")
            full_text = "\n".join(all_lines)
            limit = 4000; chunk = ""
            for line in full_text.split("\n"):
                if len(chunk) + len(line) + 1 > limit:
                    if chunk: await q.message.reply_text(chunk.strip(), parse_mode="HTML"); await asyncio.sleep(0.15)
                    chunk = line
                else:
                    chunk = chunk + "\n" + line if chunk else line
            if chunk.strip(): await q.message.reply_text(chunk.strip(), parse_mode="HTML")

        elif action == "view_files":
            all_lines = ["<b>Files Stock</b>\n"]
            for k in CAT_ORDER:
                cat = MENU.get(k, {})
                if not cat.get("products"): continue
                all_lines.append(f"<b>{esc(cat['label'])}</b>")
                for i, p in enumerate(cat["products"]):
                    f_item = get_file(k, i, d)
                    dot    = "[+]" if f_item else "[-]"
                    fname  = f_item.get("name", "?") if f_item else "none"
                    all_lines.append(f"  {dot} {esc(p['name'])}: <b>{esc(fname)}</b>")
                all_lines.append("")
            full_text = "\n".join(all_lines)
            limit = 4000; chunk = ""
            for line in full_text.split("\n"):
                if len(chunk) + len(line) + 1 > limit:
                    if chunk: await q.message.reply_text(chunk.strip(), parse_mode="HTML"); await asyncio.sleep(0.15)
                    chunk = line
                else:
                    chunk = chunk + "\n" + line if chunk else line
            if chunk.strip(): await q.message.reply_text(chunk.strip(), parse_mode="HTML")

        elif action == "add_bal":
            set_state(d, uid, "add_bal")
            await q.message.reply_text("<b>Add Balance</b>\n\nSend: <code>USER_ID AMOUNT</code>",
                parse_mode="HTML")

        elif action == "ded_bal":
            set_state(d, uid, "ded_bal")
            await q.message.reply_text("<b>Deduct Balance</b>\n\nSend: <code>USER_ID AMOUNT</code>",
                parse_mode="HTML")

        elif action == "chk_bal":
            set_state(d, uid, "chk_bal")
            await q.message.reply_text("<b>Check Balance</b>\n\nSend the User ID:")

        elif action == "add_admin":
            set_state(d, uid, "admin_id")
            await q.message.reply_text("<b>Add Admin</b>\n\nSend the Telegram User ID of the new admin:")

        elif action == "edit_price":
            clear_state(d, uid)
            await q.message.reply_text("<b>Edit Price</b>\n\nSelect a category:",
                parse_mode="HTML", reply_markup=kb_adm_cats_price())

        elif action == "edit_reseller_price":
            clear_state(d, uid)
            await q.message.reply_text(
                "<b>Edit Reseller Price</b>\n\n"
                "Set custom prices that resellers see.\nIf not set, resellers see the same price as everyone else.\n\n"
                "Select a category:",
                parse_mode="HTML", reply_markup=kb_adm_cats_reseller_price())

        elif action == "add_reseller":
            clear_state(d, uid)
            set_state(d, uid, "add_reseller")
            await q.message.reply_text(
                "<b>Add Reseller</b>\n\n"
                "Send the Telegram <b>User ID</b> of the reseller:\n\n"
                "After adding, use <b>Edit Reseller Prices</b> to set their custom prices.",
                parse_mode="HTML")

        elif action == "rem_reseller":
            resellers = d.get("resellers", {})
            if not resellers:
                await q.answer("No resellers yet.", show_alert=True); return
            await q.message.reply_text(
                "<b>Remove Reseller</b>\n\nSelect a reseller to remove:",
                parse_mode="HTML", reply_markup=kb_list_resellers(d))

        elif action == "view_resellers":
            await q.answer()
            resellers = d.get("resellers", {})
            back_kb = InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="adm|reseller_mgmt")]])
            if not resellers:
                try: await q.edit_message_text("<b>Resellers</b>\n\nNo resellers added yet.", parse_mode="HTML", reply_markup=back_kb)
                except Exception: await q.message.reply_text("<b>Resellers</b>\n\nNo resellers added yet.", parse_mode="HTML", reply_markup=back_kb)
                return
            lines = ["<b>Resellers</b>\n"]
            rp = d.get("reseller_prices", {})
            for uid_str, info in resellers.items():
                name = info.get("name", "")
                name_part = f" — {esc(name)}" if name else ""
                custom_count = sum(1 for k in rp if k.startswith(f""))
                lines.append(f"ID: <code>{uid_str}</code>{name_part}")
            if rp:
                lines.append(f"\n<b>Custom Prices Set:</b> {len(rp)} slots")
            try: await q.edit_message_text("\n".join(lines), parse_mode="HTML", reply_markup=back_kb)
            except Exception: await q.message.reply_text("\n".join(lines), parse_mode="HTML", reply_markup=back_kb)

        elif action == "broadcast":
            set_state(d, uid, "broadcast")
            await q.message.reply_text("<b>Broadcast</b>\n\nType your broadcast message:")

        elif action == "set_upi_qr":
            set_state(d, uid, "set_upi_qr")
            await q.message.reply_text("<b>Set UPI QR</b>\n\nSend the UPI QR image as a photo:")

        elif action == "set_bnb_id":
            set_state(d, uid, "set_bnb_id")
            await q.message.reply_text(
                f"<b>Set Binance ID</b>\n\nCurrent: <code>{esc(binance_id(d))}</code>\n\nSend the new Binance ID:",
                parse_mode="HTML")

        elif action == "set_support":
            set_state(d, uid, "set_support")
            await q.message.reply_text(
                f"<b>Set Support</b>\n\nCurrent: <code>{esc(support_contact(d))}</code>\n\nSend the new support contact:",
                parse_mode="HTML")

        elif action == "set_shop_name":
            set_state(d, uid, "set_shop_name")
            await q.message.reply_text(
                f"<b>Set Shop Name</b>\n\nCurrent: <b>{esc(shop_name(d))}</b>\n\nSend the new shop name:",
                parse_mode="HTML")

        elif action == "pending":
            pending = d.get("pending_orders", {})
            if not pending:
                await q.answer("No pending orders.", show_alert=True); return
            lines = ["<b>Pending Orders</b>\n"]
            for oid, order in pending.items():
                cat   = MENU.get(order["k"], {})
                prods = cat.get("products", [])
                pname = prods[order["i"]]["name"] if order["i"] < len(prods) else "?"
                lines.append(
                    f"ID: <code>{oid}</code>\n"
                    f"User: <code>{order['user_id']}</code>\n"
                    f"{esc(pname)} - {esc(order['dur'])} - ${esc(order['price'])}\n"
                    f"Method: {esc(order['method'])}\n"
                )
            await q.message.reply_text("\n".join(lines)[:4096], parse_mode="HTML")

        elif action == "clear":
            await q.message.reply_text(
                "<b>Clear ALL keys?</b> This cannot be undone.", parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Yes, clear all", callback_data="adm|confirm_clear"),
                    InlineKeyboardButton("Cancel",         callback_data="adm|cancel"),
                ]]))

        elif action == "confirm_clear":
            d["keys"] = {}; save(d)
            try: await q.edit_message_text("All keys cleared.")
            except Exception: await q.message.reply_text("All keys cleared.")

        elif action == "reseller_mgmt":
            await q.answer()
            try: await q.edit_message_text(f"<b>Admin Panel - {esc(shop_name(d))}</b>", parse_mode="HTML", reply_markup=kb_admin())
            except Exception: await q.message.reply_text(f"<b>Admin Panel - {esc(shop_name(d))}</b>", parse_mode="HTML", reply_markup=kb_admin())

        elif action == "view_users":
            await q.answer()
            all_users = d.get("all_users", {})
            verified  = d.get("verified", [])
            banned    = d.get("banned_users", [])
            back_kb   = InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="adm|cancel")]])
            if not all_users:
                try: await q.edit_message_text("<b>All Users</b>\n\nNo users yet.", parse_mode="HTML", reply_markup=back_kb)
                except Exception: await q.message.reply_text("<b>All Users</b>\n\nNo users yet.", parse_mode="HTML", reply_markup=back_kb)
                return
            lines = [f"<b>All Users</b> — {len(all_users)} total\n"]
            for uid_str, info in list(all_users.items())[-50:]:
                uid_int  = int(uid_str)
                uname    = f"@{esc(info['username'])}" if info.get("username") else "no username"
                ban_tag  = "  [BANNED]" if uid_int in banned else ""
                role_tag = " [OWNER]" if uid_int in OWNER_IDS else (" [ADMIN]" if uid_int in d.get("admin_ids",[]) else "")
                lines.append(f"<b>{esc(info.get('name','?'))}</b> {uname}{role_tag}{ban_tag}\nID: <code>{uid_str}</code> | Joined: {esc(info.get('joined','?'))}\n")
            try: await q.message.reply_text("\n".join(lines)[:4096], parse_mode="HTML", reply_markup=back_kb)
            except Exception: pass

        elif action == "ban_user":
            await q.answer()
            set_state(d, uid, "ban_user")
            await q.message.reply_text(
                "<b>Ban User</b>\n\nSend the Telegram ID of the user to ban:",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel", callback_data="adm|cancel")]]))

        elif action == "unban_user":
            await q.answer()
            banned = d.get("banned_users", [])
            if not banned:
                await q.answer("No banned users.", show_alert=True); return
            set_state(d, uid, "unban_user")
            await q.message.reply_text(
                f"<b>Unban User</b>\n\nBanned IDs: {', '.join(str(x) for x in banned)}\n\nSend the Telegram ID to unban:",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel", callback_data="adm|cancel")]]))

        elif action == "cancel":
            clear_state(d, uid)
            try: await q.edit_message_text("Cancelled.")
            except Exception: await q.message.reply_text("Cancelled.")
        return

# ═══════════════════════════════════════════════════════════════════
#  ERROR HANDLER
# ═══════════════════════════════════════════════════════════════════
async def on_error(update: object, ctx: ContextTypes.DEFAULT_TYPE):
    err = ctx.error
    if isinstance(err, (Conflict, NetworkError, TimedOut)):
        logger.warning(f"Transient: {err}"); return
    logger.error(f"Error: {err}", exc_info=err)

# ═══════════════════════════════════════════════════════════════════
#  POST INIT
# ═══════════════════════════════════════════════════════════════════
async def post_init(app):
    commands = [
        BotCommand("start",   "Open main menu"),
        BotCommand("help",    "Get help"),
        BotCommand("admin",   "Admin panel"),
        BotCommand("addbal",  "Add balance (admin)"),
        BotCommand("rembal",  "Remove balance (admin)"),
    ]
    await app.bot.set_my_commands(commands)
    await app.bot.set_chat_menu_button(menu_button=MenuButtonCommands())
    logger.info("Bot commands set.")

# ═══════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════
def main():
    try:
        result = subprocess.run(["pgrep", "-f", "python3 bot.py"], capture_output=True, text=True)
        for pid_str in result.stdout.strip().splitlines():
            pid = int(pid_str.strip())
            if pid != os.getpid():
                try: os.kill(pid, signal.SIGTERM)
                except Exception: pass
    except Exception: pass

    for _f in [DATA_FILE, DATA_FILE + ".tmp", "bot_persistence"]:
        if Path(_f).exists():
            try: os.chmod(_f, 0o666)
            except Exception: pass

    persistence = PicklePersistence(filepath="bot_persistence")
    app = (ApplicationBuilder()
           .token(BOT_TOKEN)
           .persistence(persistence)
           .post_init(post_init)
           .read_timeout(30)
           .write_timeout(30)
           .connect_timeout(30)
           .build())

    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("help",   cmd_help))
    app.add_handler(CommandHandler("admin",  cmd_admin))
    app.add_handler(CommandHandler("addbal", cmd_addbal))
    app.add_handler(CommandHandler("rembal", cmd_rembal))
    app.add_handler(CallbackQueryHandler(handle_cb))
    app.add_handler(MessageHandler(
        (filters.PHOTO | filters.Document.ALL | filters.VIDEO) & filters.ChatType.PRIVATE,
        handle_media))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
        handle_text))
    app.add_error_handler(on_error)

    logger.info("Bot starting...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
