import json
from fuzzywuzzy import process
from word2number import w2n

with open('macros.json', 'r') as f:
    MACROS = json.load(f)

def check_for_macro_command(words, i):
    """Check if the current position contains a macro insertion command."""
    if i >= len(words) - 1:
        return False
        
    # Define variations of macro insertion commands
    insert_variations = ['insert', 'add', 'include']
    macro_variations = ['macro', 'macros', 'macro:', 'macros:']
    
    # Check current word against insert variations
    current_word = words[i].lower().rstrip(',:')
    next_word = words[i + 1].lower().rstrip(',:')
    
    # Direct match check
    if current_word in insert_variations and next_word in macro_variations:
        return True
        
    # Fuzzy match check for cases with typos
    best_insert_match = process.extractOne(current_word, insert_variations)
    best_macro_match = process.extractOne(next_word, macro_variations)
    
    return (best_insert_match and best_macro_match and 
            best_insert_match[1] > 85 and best_macro_match[1] > 85)

def insert_macro(words, i, MACROS):
    for length in range(4, 0, -1):
        if i + 2 + length <= len(words):
            macro_key = ' '.join(words[i+2:i+2+length])
            # Remove trailing punctuation and normalize
            macro_key = macro_key.rstrip(',.!?').lower()
            
            # Get all keys of similar length for comparison
            same_length_keys = [key for key in MACROS.keys() 
                              if len(key.split()) == len(macro_key.split())]
            
            # Try exact match first
            if macro_key in [k.lower() for k in same_length_keys]:
                exact_key = next(k for k in same_length_keys if k.lower() == macro_key)
                return MACROS[exact_key], len(macro_key.split())
                
            # If no exact match, try fuzzy matching
            best_match = process.extractOne(macro_key, same_length_keys)
            if best_match and best_match[1] > 80:
                return MACROS[best_match[0]], len(macro_key.split())

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
            if skip > 0:
                skip -= 1
                i += 1
                continue

            word = words[i]
            word_lower = word.lower()

            # Check for replacement phrases
            phrase = ' '.join(words[i:i+2]).lower()
            best_match = process.extractOne(phrase, replace_phrases.keys())
            if best_match and best_match[1] > 95:
                final_line.append(replace_phrases[best_match[0]])
                skip = 1
                i += 2
                continue
            else:
                best_match = process.extractOne(word_lower, replace_phrases.keys())
                if best_match and best_match[1] > 95:
                    final_line.append(replace_phrases[best_match[0]])
                    i += 1
                    continue

            # Check for numbered lists
            if i < len(words) - 1 and (
                words[i+1].lower() in ["period", ".", "period.", "period,"]
            ):
                try:
                    number = w2n.word_to_num(word_lower.replace(",", ""))
                    final_line.append("\n" + str(number) + ".")
                    skip = 1
                    i += 2
                    continue
                except ValueError:
                    pass

            # Check for macro insertion
            if check_for_macro_command(words, i):
                macro_text, skip = insert_macro(words, i, MACROS)
                final_line.append(macro_text)
                i += 2 + skip
                # Handle trailing punctuation
                if i < len(words) and words[i] in [',', '.', '!', '?']:
                    final_line.append(words[i])
                    i += 1
            else:
                final_line.append(word)
                i += 1

        final_text.append(' '.join(final_line))

    # Clean up the final text
    final_text = '  \n'.join(final_text)
    final_text = (final_text.replace(" .", ".").replace(" /", "/")
                 .replace("/ ", "/").replace(" ,", ",")
                 .replace(".,", ".").replace(",.", ".")
                 .replace("..", ".").replace("( ", "(")
                 .replace(" )", ")"))

    return final_text