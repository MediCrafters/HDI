import re
import pandas as pd
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS





def basic_cleaning(text):
    # Convert to lowercase, remove non-alphanumeric characters, and extra spaces
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def remove_stopwords(text, stopwords):
    # Split text into words and manually check for stopwords to simplify the loop
    words = text.split()
    filtered_words = [word for word in words if word not in stopwords]
    return ' '.join(filtered_words)

def load_abbreviation_dict(csv_file):
    # Read the CSV into a DataFrame
    df = pd.read_csv(csv_file)
    # Convert the DataFrame into a dictionary (abbreviation -> full form)
    abbrev_dict = pd.Series(df['full_form'].values, index=df['abbrevation']).to_dict()
    return abbrev_dict

def expand_abbreviations(text, abbrev_dict):
    # Split the text into words and expand abbreviations using the abbreviation dictionary
    words = text.split()
    expanded_text = [abbrev_dict.get(word, word) for word in words]
    return ' '.join(expanded_text)

def custom_preprocessing(text, abbrev_dict, stopwords, medical_terms):
    # Apply basic cleaning, expand abbreviations, and remove stopwords
    text = basic_cleaning(text)
    text = expand_abbreviations(text, abbrev_dict)
    text = remove_stopwords(text, stopwords)
    return text
