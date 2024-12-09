# -*- coding: utf-8 -*-
"""MDI.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1g88Fs0iAfe9HcRab0IbFPE3VFOS3Rj37

Created dataset for medical terms and their explanations using web scraping techniques on the medline plus website.
created a manual dictionary and saved it to a csv file which has medical abbreviations and their full forms.
Loaded the datasets required.(medical dataset which has transcriptions, and the created datasets.)
applied pre processing tasks on both medical terms dataset and dataset with transcriptions.
used biobert,clinical bert models and tried to extract medical entities from the transcriptions.
"""


import pandas as pd
reports = pd.read_csv("/content/drive/MyDrive/NLP/Healthcare Documentation Database.csv")
print(reports)
terms = pd.read_csv("/content/drive/MyDrive/NLP/medlineplus_medical_terms.csv")
print(terms)
abbrevations = pd.read_csv("/content/drive/MyDrive/NLP/medical_abbrevations.csv")
print(abbrevations)

"""Pre Processing Medical terms dataset

"""

abbrevations = pd.read_csv("/content/drive/MyDrive/NLP/medical_abbrevations.csv")
abbrevations.head()
terms.head()

import pandas as pd
import re


terms = pd.read_csv("/content/drive/MyDrive/NLP/medlineplus_medical_terms.csv")
abbrevations = pd.read_csv("/content/drive/MyDrive/NLP/medical_abbrevations.csv")

def clean_term(term):

    term = term.lower()
    term = re.sub(r'[^a-zA-Z0-9\s]', '', term)
    term = re.sub(r'\s+', ' ', term).strip()

    for index, row in abbrevations.iterrows():
        abbrev = row['abbrevation']
        full_form = row['full_form']
        term = term.replace(abbrev, full_form)
    return term


terms['Medical Term'] = terms['Medical Term'].apply(clean_term)


terms.dropna(subset=['Explanation'], inplace=True)

terms.to_csv('/content/drive/MyDrive/NLP/cleaned_medical_terms.csv', index=False)

print(terms)

"""Pre Processing reports Dataset

"""

import pandas as pd
import re
from nltk.corpus import stopwords
import nltk

nltk.download('stopwords')

stop_words = set(stopwords.words('english'))

def clean_text(text):

    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = ' '.join([word for word in text.split() if word not in stop_words])
    return text


reports['processed_transcription'] = reports['transcription'].apply(clean_text)
print(reports[['processed_transcription', 'cleaned_transcription']])

reports.columns

reports.drop(columns=['Serial No', 'cleaned_transcription', 'description'], inplace=True)

reports.to_csv("/content/drive/MyDrive/NLP/cleaned_healthcare_reports.csv", index=False)

import pandas as pd
import re
import nltk

reports = pd.read_csv("/content/drive/MyDrive/NLP/cleaned_healthcare_reports.csv")

nltk.download('punkt')
from nltk.tokenize import word_tokenize, sent_tokenize

def tokenize(text):
   tokens = word_tokenize(text)
   return tokens
reports['tokenized_transcription'] = reports['processed_transcription'].apply(tokenize)


print(reports[['processed_transcription', 'tokenized_transcription']])
reports.to_csv("/content/drive/MyDrive/NLP/cleaned_healthcare_reports.csv", index=False)

reports.to_csv("/content/drive/MyDrive/NLP/cleaned_healthcare_reports.csv", index=False)

reports.head()

"""NER MODEL"""

import pandas as pd
reports = pd.read_csv("/content/drive/MyDrive/NLP/cleaned_healthcare_reports.csv")
terms = pd.read_csv("/content/drive/MyDrive/NLP/cleaned_medical_terms.csv")
reports.head()

medical_terms_set = set(terms['Medical Term'].str.lower())
def label_medical_terms(tokens):
    labels = []
    for token in tokens:
        if token in medical_terms_set:
            labels.append('B-MED')
        else:
            labels.append('O')
    return labels

reports['ner_labels'] = reports['tokenized_transcription'].apply(lambda x: label_medical_terms(x))


reports[['tokenized_transcription', 'ner_labels']].head()

b_med_tokens = []
for index, row in reports.iterrows():
    tokens = row['tokenized_transcription']
    labels = row['ner_labels']
    for token, label in zip(tokens, labels):
        if label == 'B-MED':
            b_med_tokens.append(token)


print("Unique B-MED tokens:", set(b_med_tokens))


"""Matching transcriptions and term explanations using semantic search
* creating embeddings for medical terms and explanations, transcriptions
* finding similarity between embeddings and matching the transcriptions with similar explanations

"""

!pip install huggingface
!pip install sentence-transformers
!pip install torch

import pandas as pd
reports = pd.read_csv("/content/drive/MyDrive/NLP/cleaned_healthcare_reports.csv")
terms = pd.read_csv("/content/drive/MyDrive/NLP/cleaned_medical_terms.csv")

terms['combined_text'] = terms['Medical Term'] + ": " + terms['Explanation']

terms.to_csv("/content/drive/MyDrive/NLP/cleaned1_medical_terms.csv", index=False)
terms.head()

import torch
from sentence_transformers import SentenceTransformer
import pickle

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

terms['embedding'] = terms['combined_text'].apply(lambda x: model.encode(x, convert_to_tensor=True))
term_embeddings = terms['embedding']

with open('/content/drive/MyDrive/NLP/term-embeddings.pkl', "wb") as fOut:
    pickle.dump(term_embeddings, fOut)

reports['embedding'] = reports['processed_transcription'].apply(lambda x: model.encode(x, convert_to_tensor=True))

reports_embeddings = reports['embedding']

with open('/content/drive/MyDrive/NLP/reports-embeddings.pkl', "wb") as fOut:
    pickle.dump(reports_embeddings, fOut)

terms.to_csv("/content/drive/MyDrive/NLP/cleaned_medical_terms.csv", index=False)
reports.to_csv("/content/drive/MyDrive/NLP/cleaned_healthcare_reports.csv", index=False)

terms.columns

"""loading embeddings"""

with open('/content/drive/MyDrive/NLP/term-embeddings.pkl', "rb") as fIn:
    term_embeddings = pickle.load(fIn)

with open('/content/drive/MyDrive/NLP/reports-embeddings.pkl', "rb") as fIn:
    reports_embeddings = pickle.load(fIn)

from sentence_transformers import util

def find_best_matches(transcription, terms_df, model, top_k=5):

    transcription_embedding = model.encode(transcription, convert_to_tensor=True)

    hits = util.semantic_search(transcription_embedding, list(terms_df['embedding']), top_k=top_k)

    if hits and len(hits) > 0:
        best_match_indices = hits[0]
        best_match_indices = [match['corpus_id'] for match in best_match_indices]
        best_matches = terms_df.iloc[best_match_indices][['Medical Term', 'Explanation']].values.tolist()

        return best_matches[0]

    else:
      return None

reports['best_matches'] = reports['processed_transcription'].apply(lambda x: find_best_matches(x, terms, model))


def extract_best_matches(x):
    if x is not None:
        return pd.Series(x)
    else:
        return pd.Series([None, None])


reports[['best_medical_term', 'best_explanation']] = reports['best_matches'].apply(extract_best_matches)


reports.to_csv("/content/drive/MyDrive/NLP/cleaned1_healthcare_reports.csv", index=False)

reports.head()

"""tokenizing using biobert model

"""

from transformers import BertTokenizer, BertForTokenClassification
import torch


tokenizer = BertTokenizer.from_pretrained("dmis-lab/biobert-v1.1")
model = BertForTokenClassification.from_pretrained("dmis-lab/biobert-v1.1")

import pandas as pd
reports = pd.read_csv("/content/drive/MyDrive/NLP/cleaned1_healthcare_reports.csv")
terms = pd.read_csv("/content/drive/MyDrive/NLP/cleaned_medical_terms.csv")

reports.shape

def preprocess_transcription(transcription):

    inputs = tokenizer(transcription, return_tensors="pt", truncation=True, padding=True)
    return inputs
def predict_entities(inputs):
    with torch.no_grad():
        outputs = model(**inputs)
    logits = outputs.logits
    predictions = torch.argmax(logits, dim=2)
    return predictions
def decode_predictions(predictions, inputs):
    predicted_labels = []
    for i, prediction in enumerate(predictions[0]):
        label = model.config.id2label[prediction.item()]
        predicted_labels.append(label)
    return predicted_labels
def extract_entities(transcription):
    inputs = preprocess_transcription(transcription)
    predictions = predict_entities(inputs)
    entities = decode_predictions(predictions, inputs)
    return entities

reports['extracted_entities'] = reports['transcription'].apply(extract_entities)


extracted_entities = reports['extracted_entities'].apply(pd.Series)

extracted_entities.columns = [f'entity_{i+1}' for i in range(extracted_entities.shape[1])]


reports = pd.concat([reports, extracted_entities], axis=1)
reports.to_csv("/content/drive/MyDrive/NLP/cleaned2_healthcare_reports.csv", index=False)

extracted_entities.shape

extracted_entities.to_csv("/content/drive/MyDrive/NLP/entities_reports.csv", index=False)

import pandas as pd
extracted_entities = pd.read_csv("/content/drive/MyDrive/NLP/entities_reports.csv")
reports = pd.read_csv("/content/drive/MyDrive/NLP/cleaned2_healthcare_reports.csv")
terms = pd.read_csv("/content/drive/MyDrive/NLP/cleaned_medical_terms.csv")

print(reports['extracted_entities'])

tokenizer = BertTokenizer.from_pretrained("dmis-lab/biobert-v1.1")
model = BertForTokenClassification.from_pretrained("dmis-lab/biobert-v1.1")

def preprocess_transcription(transcription):

    inputs = tokenizer(transcription, return_tensors="pt", truncation=True, padding=True)
    return inputs
reports['btokens'] = reports['transcription'].apply(preprocess_transcription)

reports.shape
reports.to_csv("/content/drive/MyDrive/NLP/cleaned3_healthcare_reports.csv", index=False)

reports = pd.read_csv("/content/drive/MyDrive/NLP/cleaned3_healthcare_reports.csv")

reports['btokens']
