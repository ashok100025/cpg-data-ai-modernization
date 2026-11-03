"""Deterministic synthetic data for the CPG PoC.

Writes landing files that look like what the client's systems actually send:

  data/raw/landing/pos/batch=YYYY-MM/pos_sales.csv        store POS (schema A, local time, returns as +qty)
  data/raw/landing/ecom/batch=YYYY-MM/ecom_orders.csv     e-commerce (schema B, UTC, refunds as -qty, other ids)
  data/raw/landing/erp_product/extract=YYYY-MM-01/*.csv   ERP product master (owns status, pack size, launch date)
  data/raw/landing/pim_product/extract=YYYY-MM-01/*.csv   PIM product master (owns brand, category)
  data/raw/landing/store_ref/extract=YYYY-MM-01/*.csv     store -> region reference (a store moves region)
  data/raw/landing/promotions/promotions.csv              trade promotions

Faults are injected on purpose so quality rules have something to catch:
  retries (exact duplicates), corrections (re-sent lines with new values), late arrivals,
  schema drift (new column, numbers sent as '3.0'), unknown SKUs, negative prices, missing store.

`--demo-batch` additionally lands the October 2026 batch used in the demo to show an
incremental run with late data, corrections and quality failures.
Same seed -> byte-identical files.
"""
from __future__ import annotations

import argparse
import csv
import math
import random
from datetime import date, datetime, timedelta
from pathlib import Path

SEED = 20261103
START = date(2025, 1, 6)       # a Monday
END = date(2026, 9, 27)        # a Sunday; last full week of history
DEMO_END = date(2026, 10, 25)  # the demo batch adds October 2026
INR_PER_AED = 22.6

REGIONS = ["NORTH", "SOUTH", "WEST", "EAST", "UAE"]
# store_code, name, region, utc_offset_min, currency, size factor
STORES = [
    ("S001", "Delhi Saket", "NORTH", 330, "INR", 1.3),
    ("S002", "Noida Sec 18", "NORTH", 330, "INR", 1.0),
    ("S003", "Pune Hinjewadi", "SOUTH", 330, "INR", 0.9),   # reassigned SOUTH -> WEST on 2026-07-01
    ("S004", "Bengaluru Whitefield", "SOUTH", 330, "INR", 1.4),
    ("S005", "Chennai OMR", "SOUTH", 330, "INR", 1.0),
    ("S006", "Mumbai Andheri", "WEST", 330, "INR", 1.5),
    ("S007", "Ahmedabad SG Hwy", "WEST", 330, "INR", 0.8),
    ("S008", "Kolkata Salt Lake", "EAST", 330, "INR", 1.0),
    ("S009", "Bhubaneswar", "EAST", 330, "INR", 0.6),
    ("S010", "Hyderabad Hitech", "SOUTH", 330, "INR", 1.2),
    ("S011", "Dubai Marina", "UAE", 240, "AED", 0.9),
    ("S012", "Sharjah City", "UAE", 240, "AED", 0.6),
]
REASSIGN_STORE, REASSIGN_TO, REASSIGN_FROM_DATE = "S003", "WEST", date(2026, 7, 1)
# e-commerce fulfilment nodes and the store each one is attributed to
FULFILMENT_NODES = {"FN-01": "S001", "FN-02": "S004", "FN-03": "S006", "FN-04": "S011"}

CATEGORIES = {
    "Beverages": ("Sunfresh", [("Orange Juice", "1L", 120), ("Mango Drink", "600ml", 45), ("Iced Tea", "500ml", 60),
                               ("Cola", "2L", 95), ("Coconut Water", "1L", 110), ("Lemon Soda", "750ml", 40),
                               ("Energy Drink", "250ml", 125), ("Cold Coffee", "200ml", 50), ("Apple Juice", "1L", 130),
                               ("Mineral Water", "1L", 20)]),
    "Snacks": ("CrunchCo", [("Salted Chips", "52g", 20), ("Masala Chips", "90g", 30), ("Nachos", "150g", 99),
                            ("Roasted Peanuts", "200g", 60), ("Bhujia", "400g", 110), ("Cookies", "250g", 45),
                            ("Granola Bar", "6x30g", 180), ("Popcorn", "100g", 50), ("Trail Mix", "200g", 220),
                            ("Crackers", "120g", 35)]),
    "Personal Care": ("PureGlow", [("Face Wash", "100ml", 199), ("Shampoo", "340ml", 285), ("Conditioner", "180ml", 230),
                                   ("Body Lotion", "400ml", 320), ("Soap Bar", "4x100g", 160), ("Toothpaste", "150g", 95),
                                   ("Deodorant", "150ml", 210), ("Hand Wash", "200ml", 99), ("Sunscreen", "50ml", 399),
                                   ("Hair Oil", "300ml", 175)]),
    "Home Care": ("Shinex", [("Dish Liquid", "500ml", 115), ("Detergent", "1kg", 180), ("Floor Cleaner", "1L", 199),
                             ("Glass Cleaner", "500ml", 99), ("Toilet Cleaner", "1L", 165), ("Fabric Softener", "860ml", 225),
                             ("Air Freshener", "220ml", 190), ("Bleach", "500ml", 75), ("Scrub Pads", "3pc", 60),
                             ("Garbage Bags", "30pc", 120)]),
}
# month -> multiplier per category (Indian summer for beverages, festive Oct/Nov)
SEASON = {
    "Beverages": [0.8, 0.9, 1.1, 1.4, 1.6, 1.4, 1.0, 0.95, 1.0, 1.15, 1.1, 0.85],
    "Snacks": [0.95, 0.95, 1.0, 1.0, 1.0, 1.0, 1.05, 1.05, 1.1, 1.35, 1.4, 1.1],
    "Personal Care": [1.0, 1.0, 1.0, 1.05, 1.1, 1.0, 0.95, 0.95, 1.0, 1.2, 1.25, 1.05],
    "Home Care": [0.95, 0.95, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.1, 1.45, 1.3, 1.0],
}
WEEKDAY = [0.85, 0.85, 0.9, 0.95, 1.1, 1.3, 1.25]   # Mon..Sun


def build_products():
    products, n = [], 0
    for cat, (brand, items) in CATEGORIES.items():
        for name, pack, price in items:
            n += 1
            launch = START - timedelta(days=400) if n % 9 else date(2025, 9, 1) + timedelta(days=7 * (n % 5))
            products.append(dict(sku=f"SKU-{n:04d}", name=f"{brand} {name}", brand=brand, category=cat,
                                 pack_size=pack, price_inr=price, launch=launch, popularity=0.4 + (n * 37 % 100) / 90))
    return products


def poisson(rng: random.Random, lam: float) -> int:
    if lam <= 0:
        return 0
    if lam > 30:
        return max(0, int(rng.gauss(lam, math.sqrt(lam)) + 0.5))
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= L:
            return k
        k += 1


def build_promotions(rng, products):
    promos, pid = [], 0
    d = START + timedelta(days=21)
    while d < END + timedelta(days=60):
        for _ in range(3):
            p = rng.choice(products)
            pid += 1
            promos.append(dict(promo_id=f"PR{pid:04d}", sku=p["sku"], region_code=rng.choice(REGIONS),
                               start_date=d, end_date=d + timedelta(days=13), discount_pct=rng.choice([10, 15, 20, 25])))
        d += timedelta(days=28)
    return promos


def region_of(store_code, region, day):
    return REASSIGN_TO if store_code == REASSIGN_STORE and day >= REASSIGN_FROM_DATE else region


def promo_for(promos, sku, region, day):
    for pr in promos:
        if pr["sku"] == sku and pr["region_code"] == region and pr["start_date"] <= day <= pr["end_date"]:
            return pr
    return None


def month_key(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def generate_sales(rng, products, promos, start, end):
    """Yield (batch_month, source, row dict) for every sales line between start and end."""
    pos_txn, ecom_order = 0, 0
    day = start
    while day <= end:
        t = (day - START).days / 365.0
        trend = 1.0 + 0.06 * t
        for code, _name, region, offset, ccy, size in STORES:
            reg = region_of(code, region, day)
            pos_txn += 1
            line_no = 0
            for p in products:
                if day < p["launch"] or (p["sku"] == "SKU-0027" and day >= date(2026, 3, 1)):  # discontinued
                    continue
                pr = promo_for(promos, p["sku"], reg, day)
                lam = 0.55 * p["popularity"] * size * WEEKDAY[day.weekday()] * SEASON[p["category"]][day.month - 1] * trend
                lam *= (1 + pr["discount_pct"] / 40) if pr else 1.0
                units = poisson(rng, lam)
                if not units:
                    continue
                price = p["price_inr"] * (1 - (pr["discount_pct"] / 100 if pr else 0))
                if ccy == "AED":
                    price = price / INR_PER_AED
                while units > 0:
                    q = min(units, rng.choice([1, 1, 1, 2, 3]))
                    units -= q
                    line_no += 1
                    ts = datetime(day.year, day.month, day.day, 9) + timedelta(seconds=rng.randint(0, 12 * 3600))
                    yield month_key(day), "pos", dict(
                        TXN_ID=f"{code}-{pos_txn:08d}", LINE_NO=line_no, TXN_TS_LOCAL=ts.strftime("%Y-%m-%d %H:%M:%S"),
                        STORE_CODE=code, SKU=p["sku"], QTY=q, UNIT_PRICE=f"{price:.2f}", CURRENCY=ccy, TXN_TYPE="SALE",
                        _offset=offset)
                    if rng.random() < 0.02:  # a return a few days later, POS sends +qty with type RETURN
                        rday = day + timedelta(days=rng.randint(1, 10))
                        if rday <= end:
                            rts = datetime(rday.year, rday.month, rday.day, 11) + timedelta(seconds=rng.randint(0, 8 * 3600))
                            yield month_key(rday), "pos", dict(
                                TXN_ID=f"{code}-R{pos_txn:07d}{line_no:02d}", LINE_NO=1,
                                TXN_TS_LOCAL=rts.strftime("%Y-%m-%d %H:%M:%S"), STORE_CODE=code, SKU=p["sku"], QTY=1,
                                UNIT_PRICE=f"{price:.2f}", CURRENCY=ccy, TXN_TYPE="RETURN", _offset=offset)
        # e-commerce: fewer, larger baskets, UTC timestamps, signed quantity
        for node, store in FULFILMENT_NODES.items():
            s = next(x for x in STORES if x[0] == store)
            for _ in range(poisson(rng, 6 * s[5] * WEEKDAY[day.weekday()] * (1 + 0.25 * t))):
                ecom_order += 1
                basket = rng.sample(products, rng.randint(1, 4))
                ts_utc = datetime(day.year, day.month, day.day, 3) + timedelta(seconds=rng.randint(0, 16 * 3600))
                for seq, p in enumerate(basket, 1):
                    if day < p["launch"]:
                        continue
                    price = p["price_inr"] / (INR_PER_AED if s[4] == "AED" else 1)
                    q = rng.choice([1, 1, 2])
                    row = dict(order_id=f"W{ecom_order:09d}", item_seq=seq, event_time_utc=ts_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                               fulfilment_node=node, product_code="P-" + p["sku"][4:], quantity=q,
                               price_amount=f"{price:.2f}", price_ccy=s[4], event_type="order")
                    yield month_key(day), "ecom", row
                    if rng.random() < 0.03:
                        rday = day + timedelta(days=rng.randint(2, 12))
                        if rday <= end:
                            r = dict(row, item_seq=seq + 100, event_type="refund", quantity=-q,
                                     event_time_utc=(ts_utc + timedelta(days=(rday - day).days)).strftime("%Y-%m-%dT%H:%M:%SZ"))
                            yield month_key(rday), "ecom", r
        day += timedelta(days=1)


def batch_ingested_at(batch: str) -> str:
    y, m = map(int, batch.split("-"))
    nxt = date(y + (m == 12), m % 12 + 1, 1)
    return f"{nxt.isoformat()} 02:00:00"


POS_COLS = ["TXN_ID", "LINE_NO", "TXN_TS_LOCAL", "STORE_CODE", "SKU", "QTY", "UNIT_PRICE", "CURRENCY", "TXN_TYPE", "LOADED_AT"]
ECOM_COLS = ["order_id", "item_seq", "event_time_utc", "fulfilment_node", "product_code", "quantity", "price_amount",
             "price_ccy", "event_type", "ingested_at"]
DRIFT_FROM = "2026-05"   # e-commerce adds promo_code from this batch on


def write_csv(path: Path, cols, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def inject_faults(rng, batches):
    """Mutate batches in place. Returns a count of injected faults for the run summary."""
    counts = dict(retry_duplicates=0, ecom_corrections=0, late_within_window=0, late_beyond_window=0,
                  unknown_sku=0, negative_price=0, missing_store=0, numeric_as_text=0)
    months = sorted(batches)
    for i, m in enumerate(months):
        rng = random.Random(f"{SEED}-{m}")   # per-month seed: a landed batch never changes when later batches are added
        pos, ecom = batches[m]["pos"], batches[m]["ecom"]
        # retries: the POS gateway re-sends ~0.4% of lines, sometimes in the next batch
        for row in rng.sample(pos, max(1, len(pos) // 250)):
            target = batches[months[min(i + 1, len(months) - 1)]]["pos"] if rng.random() < 0.3 else pos
            target.append(dict(row)); counts["retry_duplicates"] += 1
        # corrections: e-com re-sends a line with a corrected quantity in the next batch
        if i + 1 < len(months):
            for row in rng.sample(ecom, max(1, len(ecom) // 400)):
                fixed = dict(row, quantity=int(row["quantity"]) + (1 if int(row["quantity"]) > 0 else -1))
                fixed["_ingest_override"] = batch_ingested_at(months[i + 1]).replace("02:00", "06:30")
                batches[months[i + 1]]["ecom"].append(fixed); counts["ecom_corrections"] += 1
        # bad rows
        for _ in range(2):
            r = dict(rng.choice(pos)); r["SKU"] = "SKU-9999"; r["TXN_ID"] += "X"; pos.append(r); counts["unknown_sku"] += 1
        r = dict(rng.choice(pos)); r["UNIT_PRICE"] = "-" + r["UNIT_PRICE"]; r["TXN_ID"] += "N"; pos.append(r); counts["negative_price"] += 1
        r = dict(rng.choice(pos)); r["STORE_CODE"] = ""; r["TXN_ID"] += "M"; pos.append(r); counts["missing_store"] += 1
        # schema drift on POS: one month sends quantities as decimals in text
        if m == "2025-11":
            for r in pos:
                r["QTY"] = f"{float(r['QTY']):.1f}"
            counts["numeric_as_text"] += len(pos)
    return counts


def land(root: Path, demo_batch: bool):
    rng = random.Random(SEED)
    products = build_products()
    promos = build_promotions(rng, products)
    end = DEMO_END if demo_batch else END
    batches: dict[str, dict[str, list]] = {}
    for b, src, row in generate_sales(rng, products, promos, START, end):
        batches.setdefault(b, {"pos": [], "ecom": []})[src].append(row)

    # Late arrivals: a store's POS was offline; its lines arrive one or more batches later.
    late = dict(within=0, beyond=0)
    months = sorted(batches)
    for m_src, m_dst, store, days in [("2026-03", "2026-04", "S009", (25, 31)), ("2026-08", "2026-09", "S007", (24, 31))]:
        if m_dst in batches:
            moved = [r for r in batches[m_src]["pos"] if r["STORE_CODE"] == store and days[0] <= int(r["TXN_TS_LOCAL"][8:10]) <= days[1]]
            for r in moved:
                batches[m_src]["pos"].remove(r); batches[m_dst]["pos"].append(r)
            late["within"] += len(moved)
    # S012's POS was offline on 10-11 June 2026: those lines are withheld from the June batch and
    # only arrive with the October demo batch -> beyond the 14-day restatement window.
    withheld = [r for r in batches["2026-06"]["pos"] if r["STORE_CODE"] == "S012" and r["TXN_TS_LOCAL"][8:10] in ("10", "11")]
    for r in withheld:
        batches["2026-06"]["pos"].remove(r)
    if demo_batch:
        batches["2026-10"]["pos"].extend(withheld)
        late["beyond"] += len(withheld)

    counts = inject_faults(rng, batches)
    counts["late_within_window"], counts["late_beyond_window"] = late["within"], late["beyond"]

    landing = root / "landing"
    history_end = month_key(END)
    for m, srcs in batches.items():
        if demo_batch and m <= history_end:
            continue   # landed files are immutable: demo mode only adds the new batch
        ing = batch_ingested_at(m)
        for r in srcs["pos"]:
            r["LOADED_AT"] = ing
        for r in srcs["ecom"]:
            r["ingested_at"] = r.pop("_ingest_override", ing)
            if m >= DRIFT_FROM:
                r.setdefault("promo_code", "")
        write_csv(landing / "pos" / f"batch={m}" / "pos_sales.csv", POS_COLS, srcs["pos"])
        write_csv(landing / "ecom" / f"batch={m}" / "ecom_orders.csv",
                  ECOM_COLS + (["promo_code"] if m >= DRIFT_FROM else []), srcs["ecom"])

    # Reference extracts: monthly full snapshots, as the ERP / PIM / store systems export them.
    d = date(START.year, START.month, 1)
    last = date(end.year, end.month, 1)
    while d <= last:
        ext = d.isoformat()
        if demo_batch and d <= date(END.year, END.month, 1):
            d = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
            continue
        erp, pim = [], []
        for p in products:
            if p["launch"] > d + timedelta(days=31):
                continue
            status = "DISCONTINUED" if p["sku"] == "SKU-0027" and d >= date(2026, 3, 1) else "ACTIVE"
            pack = "120g" if p["sku"] == "SKU-0012" and d >= date(2025, 8, 1) else p["pack_size"]   # real pack change
            erp.append(dict(material_id=p["sku"], material_desc=p["name"], pack_size=pack, launch_date=p["launch"].isoformat(),
                            lifecycle_status=status, extract_date=ext))
            cat = "Healthy Snacks" if p["sku"] == "SKU-0017" and d >= date(2026, 4, 1) else p["category"]  # reclassification
            pim_pack = "500 ml" if p["sku"] == "SKU-0002" else pack                                      # conflicting attribute
            pim.append(dict(sku_code=p["sku"], brand_name=p["brand"], category_name=cat, pack_size=pim_pack,
                            marketing_name=p["name"], extract_date=ext))
        write_csv(landing / "erp_product" / f"extract={ext}" / "erp_material.csv",
                  ["material_id", "material_desc", "pack_size", "launch_date", "lifecycle_status", "extract_date"], erp)
        write_csv(landing / "pim_product" / f"extract={ext}" / "pim_product.csv",
                  ["sku_code", "brand_name", "category_name", "pack_size", "marketing_name", "extract_date"], pim)
        stores = [dict(store_code=c, store_name=n, region_code=region_of(c, r, d), utc_offset_min=o, currency=cy,
                       extract_date=ext) for c, n, r, o, cy, _ in STORES]
        write_csv(landing / "store_ref" / f"extract={ext}" / "store_master.csv",
                  ["store_code", "store_name", "region_code", "utc_offset_min", "currency", "extract_date"], stores)
        d = date(d.year + (d.month == 12), d.month % 12 + 1, 1)

    if not demo_batch:
      write_csv(landing / "promotions" / "promotions.csv",
              ["promo_id", "sku", "region_code", "start_date", "end_date", "discount_pct"],
              [dict(pr, start_date=pr["start_date"].isoformat(), end_date=pr["end_date"].isoformat()) for pr in promos])

    written = {m: v for m, v in batches.items() if not (demo_batch and m <= history_end)}
    total = sum(len(s["pos"]) + len(s["ecom"]) for s in written.values())
    print(f"Landed {len(written)} monthly batches, {total:,} sales lines, {len(products)} SKUs, {len(STORES)} stores")
    print("Injected faults:", ", ".join(f"{k}={v}" for k, v in counts.items()))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/raw")
    ap.add_argument("--demo-batch", action="store_true", help="also land the Oct-2026 batch used in the demo")
    a = ap.parse_args()
    land(Path(a.out), a.demo_batch)
