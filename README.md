**Health Diagnosis Interpreter**: 
We developed a natural language processing (NLP) system to process and interpret medical information from clinical records.
Our work focused on integrating Named Entity Recognition (NER) techniques with the Unified Medical Language System (UMLS) to identify and define medical entities. 
To further enhance usability, we employed the BART-large-CNN model for summarizing complex medical text into concise and informative summaries. 
This integration aims to improve the accessibility and usability of health information for clinical decision-making, medical research, and patient care.

**Libraries and Packages required**: 
!pip install Bio-Epidemiology-NER // pre trained NER model
!pip install pandas==1.5.3
import nltk
nltk.download('punkt_tab')
!pip uninstall -y torch torchvision torchaudio
!pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 torchaudio==2.0.2+cu118 --index-url https://download.pytorch.org/whl/cu118

