import sqlite3
import requests
import os
from dotenv import load_dotenv

load_dotenv()

RANK_ORDER = {
    "CHALLENGER": 1,
    "GRANDMASTER": 2,
    "MASTER": 3,
    "DIAMOND": 4,
    "PLATINUM": 5,
    "GOLD": 6,
    "SILVER": 7,
    "BRONZE": 8,
    "IRON": 9
}
API_KEY = os.getenv("API_KEY")
conn = sqlite3.connect("guildIDs.db")


def create_db(guildID):
    stringID = "T" + str(guildID)
    c = conn.cursor()
    if not c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{stringID}'").fetchone():
        c.execute(f"""CREATE TABLE {stringID} (
                    Name text,
                    Rank text,
                    LP integer,
                    Active text,
                    RankOrder integer
                    )""")
        conn.commit()



