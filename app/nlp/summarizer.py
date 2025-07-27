def split_sentences(text: str):
    # Basic sentence splitting (improve later with spaCy if needed)
    return re.split(r'(?<=[.!?]) +', text.strip())

from transformers import AutoTokenizer, AutoModel
import torch
import re

# Load ClinicalBERT model and tokenizer
tokenizer = AutoTokenizer.from_pretrained("emilyalsentzer/Bio_ClinicalBERT")
model = AutoModel.from_pretrained("emilyalsentzer/Bio_ClinicalBERT")

def get_sentence_embedding(sentence: str):
    inputs = tokenizer(sentence, return_tensors="pt", truncation=True, max_length=128)
    with torch.no_grad():
        outputs = model(**inputs)
        # Use the [CLS] token embedding as the sentence embedding
        return outputs.last_hidden_state[:, 0, :].squeeze(0)

def summarize_note(text: str, num_sentences: int = 3) -> str:
    """
    Summarize the clinical note using ClinicalBERT embeddings and cosine similarity.
    """
    if not text.strip():
        return "Summary not available — insufficient clinical content."
    sentences = [s.strip() for s in split_sentences(text) if s.strip()]
    if len(sentences) <= num_sentences:
        return " ".join(sentences)

    # Get embeddings for all sentences
    sent_embs = [get_sentence_embedding(s) for s in sentences]
    # Get embedding for the whole document
    doc_emb = get_sentence_embedding(text)

    # Compute cosine similarity between each sentence and the document
    similarities = [torch.nn.functional.cosine_similarity(se.unsqueeze(0), doc_emb.unsqueeze(0)).item() for se in sent_embs]
    # Get indices of top N most relevant sentences
    top_indices = sorted(range(len(similarities)), key=lambda i: similarities[i], reverse=True)[:num_sentences]
    # Sort selected sentences by their order in the original text
    top_indices.sort()
    summary = " ".join([sentences[i] for i in top_indices])
    return summary
