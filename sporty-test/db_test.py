import sqlite3
from datetime import datetime, timedelta

# Connect to the database (or create a new one if it doesn't exist)
conn = sqlite3.connect("data_test.db")


# Create the 'trade' table
conn.execute("""CREATE TABLE IF NOT EXISTS trade (
    date TEXT,
    stake REAL,
    multiplier REAL,
    result TEXT,
    curr_stk_indx,
    next_stk_indx REAL    
)
""")



def insert_trade(date, stake, multiplier, result, curr_stk_indx, next_stk_indx):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO trade (date, stake, multiplier, result, curr_stk_indx, next_stk_indx) VALUES (?, ?, ?, ?, ?, ?)", (date, stake, multiplier, result, curr_stk_indx, next_stk_indx))
    conn.commit()

def get_results(use_big_data=False):
    cursor = conn.cursor()

    cursor.execute("SELECT result FROM trade")
    results = cursor.fetchall()
    numbers = [float(row[0]) for row in results ]

    profit = 0
    for i in numbers:
        profit += i
        
    return profit