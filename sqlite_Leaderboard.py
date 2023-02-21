import sqlite3
import requests

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
API_KEY = "RGAPI-02cd650c-4868-4c02-844b-f99ff83154af"

isCalled_update = False
isCalled_add = False

conn = sqlite3.connect("main.db")
c = conn.cursor()


def create_db(guildID):
    stringID = "T" + str(guildID)
    if not c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (guildID,)).fetchone():
        c.execute(f"""CREATE TABLE {stringID} (
                    Name text,
                    Rank text,
                    LP integer,
                    Active text,
                    RankOrder integer
                    )""")
        conn.commit()


# clear table
def clear_db(guildID):
    stringID = "T" + str(guildID)
    c.execute(f"DROP TABLE IF EXISTS {stringID}")
    conn.commit()


# Player
def add_player(username, region, guildID):
    if not check_player(username, guildID):
        get_info(region, username, guildID)
        conn.commit()


def remove_player(username, guildID):
    stringID = "T" + str(guildID)
    c.execute(f"DELETE FROM {stringID} WHERE Name = ?", (username,))
    conn.commit()


def check_player(username, guildID):
    stringID = "T" + str(guildID)
    c.execute(f"SELECT Name FROM {stringID} WHERE Name = ?", (username,))
    conn.commit()
    return c.fetchone()


# leaderboard
def get_leaderboard(guildID):
    stringID = "X" + str(guildID)
    try:
        c.execute(f"SELECT * FROM {stringID} ORDER BY RankOrder, LP DESC")
        conn.commit()
        return c.fetchall()
    except sqlite3.OperationalError:
        return False


def update_leaderboard(ctx, region):
    guildID = ctx.message.guild.id
    global isCalled_update
    isCalled_update = True
    stringID = "X" + str(guildID)
    c.execute(f"SELECT Name FROM {stringID}")
    conn.commit()
    users = c.fetchall()
    for user in users:
        username = user[0]
        get_info(region, username, guildID)
        conn.commit()


def get_info(region, username, guildID):
    stringID = "T" + str(guildID)
    response = requests.get(
        f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{username}?api_key={API_KEY}")
    if response.status_code == 200:
        summoner_id = response.json()["id"]
        response = requests.get(
            f"https://{region}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}?api_key={API_KEY}")
        if response.status_code == 200:
            for entry in response.json():
                if entry["queueType"] == "RANKED_SOLO_5x5":
                    active = entry["inactive"]
                    rank = entry["tier"] + " " + entry["rank"]
                    lp = entry["leaguePoints"]
                    rank_order = RANK_ORDER[entry["tier"]]
                    if isCalled_add:
                        if not c.execute(f"SELECT Name FROM {stringID} WHERE Name = ?", (username,)).fetchone():
                            c.execute(f"INSERT INTO {stringID} VALUES (?, ?, ?, ?, ?)",
                                      (username, rank, lp, active, rank_order))
                            conn.commit()
                        else:
                            print(f"Player '{username}' already exists")
                    elif isCalled_update:
                        if not c.execute(f"SELECT Name FROM {stringID} WHERE Name = ?", (username,)).fetchone():
                            c.execute(
                                f"   UPDATE {stringID} SET Rank = ?, LP = ?, Active = ?, RankOrder = ? WHERE Name = ?",
                                (rank, lp, active, rank_order, username))
                            conn.commit()
                        else:
                            print(f"Player '{username}' does not exist")
