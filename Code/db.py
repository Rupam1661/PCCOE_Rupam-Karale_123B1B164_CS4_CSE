import os, sqlite3, datetime
import config

def conn():
    os.makedirs(config.RESULTS_DIR, exist_ok=True)
    c = sqlite3.connect(config.DB_PATH)
    c.execute("""CREATE TABLE IF NOT EXISTS findings(
        id INTEGER PRIMARY KEY AUTOINCREMENT, file TEXT, line INT, rule TEXT, severity TEXT,
        title TEXT, ai_explanation TEXT, status TEXT, ts TEXT)""")
    return c

def save(f, explanation, status):
    c = conn()
    c.execute("INSERT INTO findings(file,line,rule,severity,title,ai_explanation,status,ts) VALUES(?,?,?,?,?,?,?,?)",
              (f["file"], f["line"], f["rule"], f["severity"], f["title"], explanation, status,
               datetime.datetime.now().isoformat(timespec="seconds")))
    c.commit(); c.close()

def all_findings():
    import pandas as pd
    c = conn()
    df = pd.read_sql_query("SELECT * FROM findings ORDER BY id DESC", c)
    c.close()
    return df
