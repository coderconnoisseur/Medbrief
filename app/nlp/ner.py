####THIS FILE IS DEPRECATED 
####NOW I WILL USE SUMMARIZER INSTEAD
####
import spacy

nlp = spacy.load("en_core_sci_sm")

def extract_entities(text: str):
    doc = nlp(text)

    entities = {
        "symptoms": [],
        "medications": [],
        "diagnosis": [],
        "plan": []
    }

    for sent in doc.sents:
        sent_text = sent.text.lower()

        # Simple keyword-based matching
        if any(symptom in sent_text for symptom in ["cough", "discomfort", "pain", "fever"]):
            entities["symptoms"].append(sent.text.strip())
        if any(med in sent_text for med in ["azithromycin", "mg", "tablet", "dose"]):
            entities["medications"].append(sent.text.strip())
        if any(plan in sent_text for plan in ["follow up", "follow-up", "rest", "monitor", "review", "check"]):
            entities["plan"].append(sent.text.strip())
        if any(diag in sent_text for diag in ["diagnosis", "dx", "diagnosed"]):
            entities["diagnosis"].append(sent.text.strip())

    return entities
