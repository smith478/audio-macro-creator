import streamlit as st
import json
from fuzzywuzzy import process
from word2number import w2n

st.set_page_config(layout='wide')

# Load macros
with open('macros.json', 'r') as f:
    MACROS = json.load(f)

def add_macros_sidebar(MACROS):
    st.sidebar.selectbox('Available Macros', list(MACROS.keys()))

    new_macro_key = st.sidebar.text_input('New Macro Key')
    new_macro_value = st.sidebar.text_input('New Macro Value')

    if st.sidebar.button('Add New Macro'):
        if new_macro_key and new_macro_value:
            MACROS[new_macro_key] = new_macro_value
            with open('macros.json', 'w') as f:
                json.dump(MACROS, f)

def insert_macro(words, i, MACROS):
    for length in range(4, 0, -1):
        if i + 2 + length <= len(words):
            macro_key = ' '.join(words[i+2:i+2+length])
            same_length_keys = [key for key in MACROS.keys() if len(key.split()) == length]
            best_match = process.extractOne(macro_key.lower(), same_length_keys)

            if best_match and best_match[1] > 80:
                return MACROS.get(best_match[0]), 1 + length

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

        for i in range(len(words)):
            word = words[i]
            word_lower = word.lower()

            if skip > 0:
                skip -= 1
                continue

            phrase = ' '.join(words[i:i+2]).lower()
            best_match = process.extractOne(phrase, replace_phrases.keys())
            if best_match and best_match[1] > 95:
                final_line.append(replace_phrases.get(best_match[0]))
                skip = 1
                continue
            else:
                best_match = process.extractOne(word_lower, replace_phrases.keys())
                if best_match and best_match[1] > 95:
                    final_line.append(replace_phrases.get(best_match[0]))
                    continue

            if i < len(words) - 2 and (words[i+1].lower() == "period" or words[i+1] == "." or words[i+1].lower() == "period." or words[i+1].lower() == "period,"):
                try:
                    number = w2n.word_to_num(word_lower.replace(",", ""))
                    final_line.append("\n" + str(number) + ".")
                    skip = 1
                    continue
                except ValueError:
                    pass
            elif i < len(words) - 1 and (words[i+1].lower() == "period" or words[i+1] == "." or words[i+1].lower() == "period." or words[i+1].lower() == "period,"):
                try:
                    number = w2n.word_to_num(word_lower.replace(",", ""))
                    final_line.append("\n" + str(number) + ".")
                    skip = 1
                    continue
                except ValueError:
                    pass

            if i < len(words) - 2 and word_lower == "insert" and words[i+1].lower() == "macro":
                word, skip = insert_macro(words, i, MACROS)
                final_line.append(word)
            else:
                final_line.append(word)

        final_text.append(' '.join(final_line))

    final_text = '  \n'.join(final_text)
    final_text = final_text.replace(" .", ".").replace(" /", "/").replace("/ ", "/").replace(" ,", ",")
    final_text = final_text.replace(".,", ".").replace(",.", ".").replace("..", ".")
    final_text = final_text.replace("( ", "(").replace(" )", ")")

    return final_text

def main():
    st.title('Text Processing with Macros')
    st.write('This app allows you to process text with customizable macros.')

    add_macros_sidebar(MACROS)

    input_text = st.text_area("Enter your text here:", height=200)

    if st.button('Process Text'):
        processed_text = process_text(input_text, MACROS)
        st.markdown("Processed Text:")
        st.markdown(processed_text)

        edited_text = st.text_area("Edit Processed Text:", processed_text, height=300)

if __name__ == "__main__":
    main()