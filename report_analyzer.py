# core/report_analyzer.py
import pandas as pd
from card_transaction import CardTransaction

def ebt_summary_report(transactions, ascending=True):
    if not transactions:
        return pd.DataFrame(columns=["Date", "EBT Food Stamp", "Gross", "Fee", "Net"])

    ebt_rows = []
    all_rows = []

    for t in transactions:
        row = {
            "Date": t.batch_date,
            "Gross": t.gross,
            "Fee": t.fee,
            "Net": t.net
        }
        all_rows.append(row)

        if t.card_type.strip().upper() == "EBT FOOD STAMP":
            ebt_rows.append({
                "Date": t.batch_date,
                "EBT Food Stamp": t.net
            })

    df_all = pd.DataFrame(all_rows)
    df_ebt = pd.DataFrame(ebt_rows)

    # Summarize totals
    total_all = df_all.groupby("Date", as_index=False).sum(numeric_only=True)
    total_ebt = df_ebt.groupby("Date", as_index=False).sum(numeric_only=True)

    # Merge both
    merged = pd.merge(total_all, total_ebt, on="Date", how="left")
    merged["EBT Food Stamp"] = merged["EBT Food Stamp"].fillna(0)

    # Round
    merged["EBT Food Stamp"] = merged["EBT Food Stamp"].round(2)
    merged["Gross"] = merged["Gross"].round(2)
    merged["Fee"] = merged["Fee"].round(2)
    merged["Net"] = merged["Net"].round(2)

    # Sort
    merged = merged.sort_values(by="Date", ascending=ascending)

    grand = merged[["EBT Food Stamp", "Gross", "Fee", "Net"]].sum()
    grand_row = pd.DataFrame([{
        "Date": "GRAND TOTAL",
        "EBT Food Stamp": round(grand["EBT Food Stamp"], 2),
        "Gross": round(grand["Gross"], 2),
        "Fee": round(grand["Fee"], 2),
        "Net": round(grand["Net"], 2)
    }])
    merged = merged[["Date", "EBT Food Stamp", "Gross", "Fee", "Net"]]

    return pd.concat([merged, grand_row], ignore_index=True)


def group_by_date_with_summary(transactions, ascending=True, hide_transactions=False):
    if not transactions:
        return pd.DataFrame(columns=["Date", "Card Type", "Qty", "Gross", "Net", "Fee"])

    data = [{
        "Date": t.batch_date,
        "Card Type": t.card_type,
        "Qty": t.quantity,
        "Gross": t.gross,
        "Net": t.net,
        "Fee": t.fee
    } for t in transactions]

    df = pd.DataFrame(data)
    grouped = df.groupby(["Date", "Card Type"], as_index=False).sum(numeric_only=True)
    grouped = grouped.sort_values(by="Date", ascending=ascending)

    grouped["Qty"] = grouped["Qty"].round(0).astype(int)
    grouped["Gross"] = grouped["Gross"].round(2)
    grouped["Net"] = grouped["Net"].round(2)
    grouped["Fee"] = grouped["Fee"].round(2)

    grouped["Date"] = grouped["Date"].mask(grouped["Date"].duplicated(), "")

    grand_totals = grouped[["Qty", "Gross", "Net", "Fee"]].sum(numeric_only=True)
    grand_row = pd.DataFrame([{
        "Date": "GRAND TOTAL",
        "Card Type": "",
        "Qty": int(grand_totals["Qty"]),
        "Gross": round(grand_totals["Gross"], 2),
        "Net": round(grand_totals["Net"], 2),
        "Fee": round(grand_totals["Fee"], 2)
    }])

    return grand_row if hide_transactions else pd.concat([grouped, grand_row], ignore_index=True)

def group_by_date_totals_only(transactions, ascending=True):
    if not transactions:
        return pd.DataFrame(columns=["Date", "Qty", "Gross", "Net", "Fee"])

    data = [{
        "Date": t.batch_date,
        "Qty": t.quantity,
        "Gross": t.gross,
        "Net": t.net,
        "Fee": t.fee
    } for t in transactions]

    df = pd.DataFrame(data)
    grouped = df.groupby("Date", as_index=False).sum(numeric_only=True)
    grouped = grouped.sort_values(by="Date", ascending=ascending)

    grouped["Qty"] = grouped["Qty"].round(0).astype(int)
    grouped["Gross"] = grouped["Gross"].round(2)
    grouped["Net"] = grouped["Net"].round(2)
    grouped["Fee"] = grouped["Fee"].round(2)

    grand_totals = grouped[["Qty", "Gross", "Net", "Fee"]].sum(numeric_only=True)
    grand_row = pd.DataFrame([{
        "Date": "GRAND TOTAL",
        "Qty": int(grand_totals["Qty"]),
        "Gross": round(grand_totals["Gross"], 2),
        "Net": round(grand_totals["Net"], 2),
        "Fee": round(grand_totals["Fee"], 2)
    }])

    return pd.concat([grouped, grand_row], ignore_index=True)
