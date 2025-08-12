# reports.py
import os
import sqlite3
import pandas as pd
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

DB_FILE = os.path.join(os.path.dirname(__file__), "../attendance.db")
EXPORTS_DIR = os.path.join(os.path.dirname(__file__), "exports")
os.makedirs(EXPORTS_DIR, exist_ok=True)

def fetch_df():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT name, date, time FROM attendance ORDER BY date, time", conn)
    conn.close()
    return df

def export_csv(path=None):
    df = fetch_df()
    path = path or os.path.join(EXPORTS_DIR, f"attendance_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    df.to_csv(path, index=False)
    return path

def export_excel(path=None):
    df = fetch_df()
    path = path or os.path.join(EXPORTS_DIR, f"attendance_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
    df.to_excel(path, index=False)
    return path

def export_pdf(path=None):
    df = fetch_df()
    path = path or os.path.join(EXPORTS_DIR, f"attendance_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
    data = [df.columns.tolist()] + df.values.tolist()
    doc = SimpleDocTemplate(path)
    table = Table(data)
    table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.grey),("GRID",(0,0),(-1,-1),0.25,colors.black)]))
    doc.build([table])
    return path

def monthly_summary(year, month):
    df = fetch_df()
    df['date'] = pd.to_datetime(df['date'])
    mask = (df['date'].dt.year == year) & (df['date'].dt.month == month)
    dfm = df[mask]
    if dfm.empty:
        return pd.DataFrame()
    summary = dfm.groupby('name').agg(total_days_present=('date','nunique')).reset_index()
    # To compute percentage you need number of working days — we'll return count only
    return summary
