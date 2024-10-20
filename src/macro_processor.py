import json
from fuzzywuzzy import process
from word2number import w2n

with open('macros.json', 'r') as f:
    MACROS = json.load(f)

def insert_macro(words, i, MACROS):
    for length in range(4, 0, -1):
        if i + 2 + length <= len(words):
            macro_key = ' '.join(words[i+2:i+2+length])
            # Remove trailing punctuation from the macro key
            macro_key = macro_key.rstrip(',.!?')
            same_length_keys = [key for key in MACROS.keys() if len(key.split()) == len(macro_key.split())]
            best_match = process.extractOne(macro_key.lower(), same_length_keys)

            if best_match and best_match[1] > 80:
                return MACROS.get(best_match[0]), 1 + len(macro_key.split())

    return words[i], 0

def process_text(text, MACROS):
    replace_phrases = {
        "period": ".",
        "new line": "  \n",
        "newline": "  \n",
        "slash": "/",
        "comma": ",",
        "open paren": "(",
        "closed paren": ")",
        "close paren": ")",
        "open paren.": "(",
        "closed paren.": ")",
        "close paren.": ")",
    }

    lines = text.split('\n')
    final_text = []
    skip = 0

    for line in lines:
        words = line.split()
        final_line = []

        i = 0
        while i < len(words):
            word = words[i]
            word_lower = word.lower()

            if skip > 0:
                skip -= 1
                i += 1
                continue

            phrase = ' '.join(words[i:i+2]).lower()
            best_match = process.extractOne(phrase, replace_phrases.keys())
            if best_match and best_match[1] > 95:
                final_line.append(replace_phrases.get(best_match[0]))
                skip = 1
                i += 2
                continue
            else:
                best_match = process.extractOne(word_lower, replace_phrases.keys())
                if best_match and best_match[1] > 95:
                    final_line.append(replace_phrases.get(best_match[0]))
                    i += 1
                    continue

            if i < len(words) - 2 and (words[i+1].lower() == "period" or words[i+1] == "." or words[i+1].lower() == "period." or words[i+1].lower() == "period,"):
                try:
                    number = w2n.word_to_num(word_lower.replace(",", ""))
                    final_line.append("\n" + str(number) + ".")
                    skip = 1
                    i += 2
                    continue
                except ValueError:
                    pass
            elif i < len(words) - 1 and (words[i+1].lower() == "period" or words[i+1] == "." or words[i+1].lower() == "period." or words[i+1].lower() == "period,"):
                try:
                    number = w2n.word_to_num(word_lower.replace(",", ""))
                    final_line.append("\n" + str(number) + ".")
                    skip = 1
                    i += 2
                    continue
                except ValueError:
                    pass

            if i < len(words) - 2 and word_lower == "insert" and words[i+1].lower() == "macro":
                macro_text, skip = insert_macro(words, i, MACROS)
                final_line.append(macro_text)
                i += 2 + skip
                # Check if there's a trailing punctuation after the macro
                if i < len(words) and words[i] in [',', '.', '!', '?']:
                    final_line.append(words[i])
                    i += 1
            else:
                final_line.append(word)
                i += 1

        final_text.append(' '.join(final_line))

    final_text = '  \n'.join(final_text)
    final_text = final_text.replace(" .", ".").replace(" /", "/").replace("/ ", "/").replace(" ,", ",")
    final_text = final_text.replace(".,", ".").replace(",.", ".").replace("..", ".")
    final_text = final_text.replace("( ", "(").replace(" )", ")")

    return final_text