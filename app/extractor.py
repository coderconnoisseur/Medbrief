import spacy
from scispacy.abbreviation import AbbreviationDetector
from typing import List, Dict
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# Load clinical NER model
nlp = spacy.load("en_ner_bc5cdr_md")
nlp.add_pipe("abbreviation_detector")
nlp.add_pipe("negex", config={"neg_termset": "en_clinical"})

# Load ClinicalBERT for sentence classification (assume 4 classes: symptom, medication, diagnosis, plan)
tokenizer_cls = AutoTokenizer.from_pretrained("emilyalsentzer/Bio_ClinicalBERT")
model_cls = AutoModelForSequenceClassification.from_pretrained("emilyalsentzer/Bio_ClinicalBERT", num_labels=4)

def classify_sentence(sentence: str) -> str:
    """
    Classify a sentence as 'symptom', 'medication', 'diagnosis', or 'plan' using ClinicalBERT.
    This is a placeholder: you must fine-tune the model for best results.
    """
    label_map = {0: 'symptoms', 1: 'medications', 2: 'diagnosis', 3: 'plan'}
    inputs = tokenizer_cls(sentence, return_tensors="pt", truncation=True, max_length=128)
    with torch.no_grad():
        logits = model_cls(**inputs).logits
        predicted_class = torch.argmax(logits, dim=1).item()
    return label_map[predicted_class]

def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    Extract clinical entities from text using sentence classification (ClinicalBERT).
    """
    # Split text into sentences (simple split, can use spaCy for better results)
    import re
    sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', text.strip()) if s.strip()]
    entities = {"symptoms": [], "medications": [], "diagnosis": [], "plan": []}
    for sent in sentences:
        label = classify_sentence(sent)
        entities[label].append(sent)
    # Remove duplicates while preserving order
    for k in entities:
        entities[k] = list(dict.fromkeys(entities[k]))
    return entities
