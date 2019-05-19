import sys
import sqlite3
import time
import random

def initialize_database():
    # Creates SQLite database.
    #--------------------
    conn = sqlite3.connect('translate_game.sqlite')
    cur = conn.cursor()
    conn.text_factory = str
    cur.executescript(
        '''CREATE TABLE IF NOT EXISTS words
        (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 
            russian TEXT UNIQUE NOT NULL, 
            english TEXT UNIQUE NOT NULL,
            category_id INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS categories
        (
            id INTEGER NOT NULL PRIMARY KEY, 
            name TEXT UNIQUE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS leaderboard
        (
            user_id INTEGER UNIQUE NOT NULL PRIMARY KEY,
            datetime INTEGER NOT NULL,
            score INTEGER,
            user_name TEXT NOT NULL
        );'''
    )

    conn.commit()
    conn.close()

def load_words(filename):
    # Loads words from "filename" file to the "words" database table
    # -----------------
    # words file format:
    #------------------    
    # category\n
    # russian \tenglish\n
    # russian \tenglish\n
    #------------------


    conn = sqlite3.connect('translate_game.sqlite')
    cur = conn.cursor()
    conn.text_factory = str
    with open(filename) as words_file:
        cur_id = 0
        category_set = False
        for line in words_file:
            line_words = line.replace('\n', '').split('\t')
            if (len(line_words) == 1):
                if len(line_words[0]) > 0:
                    if category_set:
                        cur_id += 1
                    cur.execute('''INSERT OR IGNORE INTO categories (id, name) VALUES (?, ?)''', \
                            (cur_id, line_words[0],))
                    category_set = True
            elif (len(line_words) != 0):
                if not category_set:
                    raise Exception('Specify category before the word list!')
                rus, eng = line_words
                cur.execute('''INSERT OR IGNORE INTO words (russian, english, category_id) VALUES (?, ?, ?)''', \
                        (rus, eng, cur_id))

    conn.commit()
    conn.close()


def create_database(words_filename):
    initialize_database()
    load_words(words_filename)
    return True
    

def update_leaderboard(update, score):
    # Updates user's previous record if the score is greater.
    # Creates new entry if there are no user's records.
    # Returns True if the leaderboard was changed.
    # -----------------

    conn = sqlite3.connect('translate_game.sqlite')
    cur = conn.cursor()
    conn.text_factory = str
    user_record = cur.execute('''SELECT score FROM leaderboard WHERE user_id = ?''',
                            (update.message.from_user.id,)).fetchone()
    updated = False
    if (not user_record is None) and len(user_record) > 0:
        if (score > user_record[0]):
            cur.execute('''UPDATE leaderboard SET score = ? WHERE user_id = ?''',
                            (score, update.message.from_user.id,))
            print('User', update.message.from_user.username, 'updated its score')
            updated = True
    else:
        name, surname = '', ''
        if (not update.message.from_user.first_name is None):
            name = update.message.from_user.first_name
        if (not update.message.from_user.last_name is None):
            name = update.message.from_user.last_name
        name = name + ' ' + surname
        cur.execute('''INSERT OR IGNORE INTO leaderboard (user_id, datetime, score, user_name) VALUES (?, ?, ?, ?)''', \
                (update.message.from_user.id, int(time.time()), score, name,))
        print('New user registered')
        updated = True
    conn.commit()
    conn.close()
    return updated

def get_leaderboard():
    # Returns the leaderboard in the following format:
    # ---------------------
    # (user_id, score, name, date)
    # ---------------------
    
    conn = sqlite3.connect('translate_game.sqlite')
    cur = conn.cursor()
    conn.text_factory = str
    
    lb = cur.execute('''SELECT * FROM leaderboard ORDER BY score DESC''').fetchall()
    conn.close()
    return lb

def get_user_record(user_id):
    # Returns users leaderboard score by id
    #----------------------
 
    conn = sqlite3.connect('translate_game.sqlite')
    cur = conn.cursor()
    conn.text_factory = str
    print('getting users id - {}'.format(user_id))
    
    lb = cur.execute('''SELECT score FROM leaderboard WHERE user_id = ?''',(user_id,)).fetchone()
    if len(lb) > 0:
        score = lb[0]
    else:
        score = 0
    conn.close()
    return score

    
def get_categories():
    # Returns the list of existing categories
    # --------------------
    
    conn = sqlite3.connect('translate_game.sqlite')
    cur = conn.cursor()
    conn.text_factory = str
    categories = cur.execute('''SELECT DISTINCT name FROM categories''').fetchall()
    conn.close()
    return categories


def get_words(category='Случайная тема'):
    # Returns the list of rus/eng word pairs of the specified category.
    # If the category is not specified, random category is used.
    # Return format - (words_list, category)
    # ------------------

    conn = sqlite3.connect('translate_game.sqlite')
    cur = conn.cursor()
    conn.text_factory = str

    if category == 'Случайная тема':
        categories = cur.execute('''SELECT DISTINCT id, name FROM categories''').fetchall()
        category_id = random.randint(0, len(categories) - 1)
        category = categories[category_id][1]
    else:
        category_id = cur.execute('''SELECT id FROM categories WHERE name = ?''',  (category,)).fetchone()[0]

    words = cur.execute('''SELECT russian, english FROM words WHERE category_id = ?''', (category_id,)).fetchall()
    conn.close()
    return words, category
