import re
import pandas as pd
import requests
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
from Bio_Epidemiology_NER.bio_recognizer import ner_prediction
from typing import List, Dict


# UMLS API Authentication and Query Functions
def get_umls_auth_token(api_key: str) -> str:
    """
    Get a Ticket-Granting Ticket (TGT) using the UMLS API key.
    """
    url = "https://utslogin.nlm.nih.gov/cas/v1/api-key"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = f'apikey={api_key}'
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    return response.headers['location']


def get_service_ticket(tgt: str) -> str:
    """
    Get a Service Ticket (ST) using the TGT.
    """
    service = "http://umlsks.nlm.nih.gov"
    response = requests.post(tgt, data={'service': service})
    response.raise_for_status()
    return response.text


def search_umls_cui(term: str, ticket: str) -> str:
    """
    Search for the CUI of a medical term.
    """
    search_endpoint = "https://uts-ws.nlm.nih.gov/rest/search/current"
    params = {
        'string': term,
        'ticket': ticket,
        'searchType': 'exact'
    }
    response = requests.get(search_endpoint, params=params)
    response.raise_for_status()
    results = response.json()
    if results['result']['results']:
        return results['result']['results'][0]['ui']
    return None


def get_umls_definitions(cui: str, ticket: str) -> List[str]:
    """
    Retrieve definitions for a CUI.
    """
    definition_endpoint = f"https://uts-ws.nlm.nih.gov/rest/content/current/CUI/{cui}/definitions"
    params = {'ticket': ticket}
    response = requests.get(definition_endpoint, params=params)
    response.raise_for_status()
    definitions = response.json()
    return [item['value'] for item in definitions['result']] if definitions['result'] else []


# Preprocessing Functions
def basic_cleaning(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def remove_stopwords(text: str, stopwords: set) -> str:
    words = text.split()
    filtered_words = [word for word in words if word not in stopwords]
    return ' '.join(filtered_words)


def load_abbreviation_dict(csv_file: str) -> Dict[str, str]:
    df = pd.read_csv(csv_file)
    return pd.Series(df['full_form'].values, index=df['abbrevation']).to_dict()


def expand_abbreviations(text: str, abbrev_dict: Dict[str, str]) -> str:
    words = text.split()
    expanded_text = [abbrev_dict.get(word, word) for word in words]
    return ' '.join(expanded_text)


def custom_preprocessing(text: str, abbrev_dict: Dict[str, str], stopwords: set) -> str:
    text = basic_cleaning(text)
    text = expand_abbreviations(text, abbrev_dict)
    text = remove_stopwords(text, stopwords)
    return text


# Main Workflow
def process_medical_text(text: str, api_key: str, abbrev_dict: Dict[str, str], stopwords: set) -> None:
    # Step 1: Preprocess the text
    doc = custom_preprocessing(text, abbrev_dict, stopwords)

    # Step 2: Extract entities using the Bio_Epidemiology_NER model
    entities_df = ner_prediction(corpus=doc, compute='cpu')

    # Step 3: Filter entities based on required tags
    required_tags = ['Disease_disorder', 'Medication', 'Sign_symptom']
    filtered_df = entities_df[entities_df['entity_group'].isin(required_tags)].reset_index(drop=True)

    # Step 4: Extract unique terms for querying definitions
    unique_terms = filtered_df['value'].unique()

    print("Detected Terms with Definitions:")
    for term in unique_terms:
        try:
            # Step 5: Query UMLS for definitions
            tgt = get_umls_auth_token(api_key)
            ticket = get_service_ticket(tgt)
            cui = search_umls_cui(term, ticket)

            if cui:
                print(f"\nTerm: {term} (CUI: {cui})")
                ticket = get_service_ticket(tgt)  # Refresh ticket for each API call
                definitions = get_umls_definitions(cui, ticket)
                if definitions:
                    for idx, definition in enumerate(definitions, 1):
                        print(f"  {idx}. {definition}")
                else:
                    print("  No definitions found.")
            else:
                print(f"\nTerm: {term}")
                print("  No CUI found.")
        except Exception as e:
            print(f"Error retrieving information for term '{term}': {e}")


# Example Usage
if __name__ == "__main__":
    # Load abbreviation dictionary from CSV
    abbrev_dict = load_abbreviation_dict('/content/drive/MyDrive/NLP/medical_abbrevations.csv')

    # Example text
    text = """
    Patient Name: John Doe
Date of Birth: 1975-05-10
Date of Examination: 2024-11-25
Examined By: Dr. Jane Smith, MD

Chief Complaint:
Persistent cough, intermittent fever, and fatigue for two weeks.

Assessment:
Suspected pneumonia. Possible COPD exacerbation.

Plan:
Chest X-ray, blood tests, sputum culture.
Antibiotics (e.g., Azithromycin), bronchodilators (e.g., Albuterol).
Smoking cessation counseling.
Follow-up in 5-7 days.

Disclaimer: This is a sample medical report and should not be considered actual medical advice.
    """

    # Process the medical text
    process_medical_text(text, API_KEY, abbrev_dict, ENGLISH_STOP_WORDS)
