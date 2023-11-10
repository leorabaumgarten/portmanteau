from flask import Flask, render_template, request, jsonify
import sqlite3
from sqlite3 import Connection
import ast
import re
import argparse
from itertools import product
from difflib import SequenceMatcher, Match

app = Flask(__name__)

DATABASE = 'database.db'

CMU_PRONUNCIATION_FILEPATH = "cmudict-0.7b.txt"

CMU_PHONEME_FILEPATH = "cmudict-0.7b.phones.txt"

SPELLINGS = {"AA": ["augh", "au", "ou", "o", "a", "al"],
            "AE": ["a"],
            "AH": ["u", "a", "o", "e", "i", "y", "ou", ""],
            "AO": ["augh", "o", "aw", "a", "au", "ou"],
            "AW": ["ou", "ow"],
            "AY": ["igh", "ie", "i", "aye", "uy", "y", "ye"],
            "B": ["be", "bb", "b"],
            "CH": ["tch", "ch", "t"],
            "D": ["d", "dd", "tt", "de", "ed"], 
            "DH": ["th", "the"],
            "EH": ["e", "a", "ie"],
            "ER": ["er", "ar", "ir", "or", "ur", "ure", "r"],
            "EY": ["ay", "ai", "a", "eigh"],
            "F": ["gh", "ff", "f", "fe"],
            "G": ["gg", "g", "gue"],
            "HH": ["h"],
            "IH": ["i", "hi", "y", "a", "e"],
            "IY": ["ea", "ee", "ie", "i", "y", "ei", "e"],
            "JH": ["g", "ge", "j"],
            "K": ["k", "ck", "ch", "c", "kh", "kk", "ke", "x"],
            "L": ["ll", "l", "le", "ol"],
            "M": ["mm", "m", "mb", "mn", "me"],
            "N": ["nn", "kn", "mn", "gn", "n", "ne"],
            "NG": ["ng", "ngue"],
            "OW": ["oa", "owe", "ow", "oe", "aoh", "oh", "o", "hoa"],
            "OY": ["oi", "oy", "aw"],
            "P": ["pp", "pe", "p"],
            "R": ["rr", "re", "wr", "r"],
            "S": ["sc", "ss", "ps", "se", "ce", "c", "s", ""],
            "SH": ["sh", "sch", "ti", "ci"],
            "T": ["tt", "te", "bt", "t"],
            "TH": ["th"],
            "UH": ["oo", "u"],
            "UW": ["ui", "oo", "ue", "ew", "ewe", "u", "ieu", "eau", "wo"],
            "V": ["vv", "ve", "v"],
            "W": ["wh", "we", "w", "u"],
            "Y": ["yy", "y", ""],
            "Z": ["zz", "ze", "se", "s", "z"],
            "ZH": ["si", "s"]}


def initialize_dictionary() -> None:
    connection = sqlite3.connect(DATABASE)
    with open('schema.sql') as f:
        connection.executescript(f.read())


def get_db_connection() -> Connection:
    connection = sqlite3.connect(DATABASE)
    return connection


def insert_into_pronunciations(connection: Connection, word: str, pronunciation: list[list[str]]) -> None:
    connection.execute("""INSERT INTO pronunciations VALUES (?, ?);""", (word, str(pronunciation)))
    connection.commit()


def insert_into_phonemes(connection: Connection, phoneme: str, sound_type: str) -> None:
    connection.execute("""INSERT INTO phonemes VALUES (?, ?);""", (phoneme, str(sound_type)))
    connection.commit()


def load_pronunciation_dictionary(filepath: str) -> None:
    with open(filepath) as file:
        lines = file.readlines()
    lines = [line.strip() for line in lines[126:]]

    pronunciation_dictionary = {}
    for line in lines:
        line = line.split()
        word = line[0].lower()
        if word.endswith(')'):
            word = word[:-3]

        pronunciation = re.findall(r"[A-Z]+", " ".join(line[1:]))
        if word in pronunciation_dictionary:
            if pronunciation not in pronunciation_dictionary[word]:
                pronunciation_dictionary[word].append(pronunciation)
        else:
            pronunciation_dictionary[word] = [pronunciation]

    connection = get_db_connection()
    for word, pronunciation in pronunciation_dictionary.items():
        insert_into_pronunciations(connection, word, pronunciation)
    return 


def load_phoneme_dictionary(filepath: str) -> None:
    with open(filepath) as file:
        lines = file.readlines()
    lines = [line.strip().split('\t') for line in lines]
    connection = get_db_connection()
    for line in lines:
        insert_into_phonemes(connection, line[0], line[1])
    return 


def load_cmu(load: bool=False) -> None:
    initialize_dictionary()
    if load:
        load_pronunciation_dictionary(CMU_PRONUNCIATION_FILEPATH)
        load_phoneme_dictionary(CMU_PHONEME_FILEPATH)
    return


def search_pronunciation(connection: Connection, word: str) -> list[list[str]]:
    pronunciations = connection.execute("""SELECT pronunciation FROM pronunciations WHERE word=?;""", (word,)).fetchall()
    if pronunciations:
        return ast.literal_eval(pronunciations[0][0])
    else: 
        return None


def search_phoneme(connection: Connection, phoneme: str) -> str:
    phonemes = connection.execute("""SELECT sound_type FROM phonemes WHERE phoneme=?;""", (phoneme,)).fetchall()
    return phonemes[0][0]


def last_resort_portmanteau(word1: str, word2: str) -> str:
    return word1[:len(word1)//2] + word2[len(word2)//2:]


def longest_common_subsequence(word1: list[str], word2: list[str]) -> Match:
    match = SequenceMatcher(None, word1, word2).find_longest_match()
    connection = get_db_connection()
    if match.a == 0 and (match.b == 0 or match.b == len(word2) - 1):
        return None
    elif match.a + match.size == len(word1) and match.b + match.size == len(word2):
        return None
    elif "vowel" not in [search_phoneme(connection, sound) for sound in word1[:match.a+match.size]] and search_phoneme(connection, word2[match.b+match.size]) != "vowel":
        return None
    elif "vowel" not in [search_phoneme(connection, sound) for sound in word2[match.b:]] and (match.a == 0 or search_phoneme(connection, word1[match.a-1]) != "vowel"):
        return None
    elif len(word1[:match.a] + word2[match.b:]) < len(word1 + word2) / 2 - 1:
        return None
    else:
        return match


def get_match(word1_pronunciations: list[list[str]], word2_pronunciations: list[list[str]]) -> tuple[Match, (list[str], list[str])]: 
    matches = []
    for word1_pronunciation in word1_pronunciations:
        for word2_pronunciation in word2_pronunciations:
            common_subsequence = longest_common_subsequence(word1_pronunciation, word2_pronunciation)
            if common_subsequence:
                matches.append((common_subsequence, (word1_pronunciation, word2_pronunciation)))
    if matches:
        return max(matches, key=lambda x: x[0].size)  
    else:
        return None
    

def blend(word1: list[str], word2: list[str], match: Match) -> tuple[list[str], list[str]]:
    return word1[:match.a + match.size], word2[match.b + match.size:]


def get_types(word1: list[str], word2: list[str]) -> tuple[list[str], list[str]]:
    connection = get_db_connection()
    return [search_phoneme(connection, phoneme) for phoneme in word1], [search_phoneme(connection, phoneme) for phoneme in word2]


def basic_portmanteau(word1: list[str], word2: list[str]) -> tuple[list[str], list[str]]:
    word1_types, word2_types = get_types(word1, word2)
    word1_vowels = [index for index, sound_type in enumerate(word1_types) if sound_type == "vowel"]
    if len(word1_vowels) > 2:
        i = round(len(word1_vowels)/2)
    else:
        i = 0
    while word1_vowels[i] == 0:
        i += 1
        if i >= len(word1_vowels):
            return [], []
    word2_vowel = word2_types.index("vowel")
    return word1[:word1_vowels[i]], word2[word2_vowel:]


def get_orthography(word: str, word_segment: list[str], end: bool=False) -> str:
    possible_spellings = SPELLINGS[word_segment[0]]
    for i in range(1, len(word_segment)):
        possible_spellings = list(product(possible_spellings, SPELLINGS[word_segment[i]]))
        possible_spellings = ["".join(spelling) for spelling in possible_spellings]
    if end:
        spellings = [spelling for spelling in possible_spellings if word.endswith(spelling)]
    else:
        spellings = [spelling for spelling in possible_spellings if word.startswith(spelling)]
    try:
        spelling = max(spellings, key=len)
        if spelling.endswith("e") and not end and len(spellings) > 1:
            spellings.remove(spelling)
            spelling = max(spellings, key=len)
        elif (spelling.startswith("ed") or spelling.startswith("ol")) and end and len(spellings) > 1:
            spellings.remove(spelling)
            spelling = max(spellings, key=len)
        return spelling
    except:
        return None


@app.route('/answer', methods=['POST'])
def get_answer():
    if request.method == 'POST':
        data = request.get_json()
        # Access specific values from the JSON data
        word1 = data.get('word1')
        word2 = data.get('word2')
        response = ""

        connection = get_db_connection()
        word1_pronunciations = search_pronunciation(connection, word1)
        word2_pronunciations = search_pronunciation(connection, word2)

        if not word1_pronunciations or not word2_pronunciations:
            words_not_found = []
            if not word1_pronunciations:
                words_not_found.append(word1)
            if not word2_pronunciations:
                words_not_found.append(word2)
            portmanteau = last_resort_portmanteau(word1, word2)
            response = {"error": f"The word(s) {words_not_found} are not present in the source dictionary. A last-resort portmanteau for {word1} and {word2} is {portmanteau}."}
        
        else:
            match = get_match(word1_pronunciations, word2_pronunciations)
            reverse = False
            phonological = True
            
            if match:
                word1_pronunciation, word2_pronunciation = match[1]
                word1_segment, word2_segment = blend(word1_pronunciation, word2_pronunciation, match[0])
            
            else:
                phonological = False
                word1_segment, word2_segment = basic_portmanteau(word1_pronunciations[0], word2_pronunciations[0])
            
            if not (word1_segment or word2_segment):
                reverse = True
                word2_segment, word1_segment = basic_portmanteau(word2_pronunciations[0], word1_pronunciation[0])
                if not (word1_segment or word2_segment):
                    response = {"error": f"There is no portmanteau that can be formed from the words {word1_segment} and {word2_segment}."}
            
            if reverse:
                word1_segment = get_orthography(word1, word1_segment, True)
                word2_segment = get_orthography(word2, word2_segment)
                portmanteau = word2_segment + word1_segment
            else:
                word1_segment = get_orthography(word1, word1_segment)
                word2_segment = get_orthography(word2, word2_segment, True)
                portmanteau =  word1_segment + word2_segment

            if not (word1_segment and word2_segment):
                weird_spellings = []
                if not word1_segment:
                    weird_spellings.append(word1)
                if not word2_segment:
                    weird_spellings.append(word2)
                portmanteau = last_resort_portmanteau(word1, word2)
                response = {"success": f"The word(s) {weird_spellings} spell their phonemes in ways we haven't accounted for yet. A last-resort portmanteau for {word1} and {word2} is {portmanteau}"}

            if phonological:
                response = {"success": f"The overlapping blend of {word1} and {word2} is {portmanteau}."}
            elif reverse:
                response = {"success": f"There is no phonologically overlapping blend of the words {word1} and {word2}, nor is there a good non-overlapping portmanteau that can be generated with {word1} first and {word2} second. A reverse-order non-overlapping portmanteau is {portmanteau}."}
            else:
                response = {"success": f"There is no phonologically overlapping blend of the words {word1} and {word2}. A non-overlapping portmanteau is {portmanteau}."}
        print(response)
        return jsonify(response)

@app.route('/', methods=['GET', 'POST'])
def run():
    return render_template('input.html')
    
@app.route('/about', methods=['GET'])
def display():
    return render_template('about.html')                
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--load', help='load the cmu dictionary from scratch', action='store_true')
    parser.add_argument('-d', '--debug', help='debug mode', action='store_true')
    args = parser.parse_args()
    LOAD = args.load
    load_cmu(LOAD)
    if args.debug:
        app.run(debug=True)
    else:
        app.run()