"""
Medical Entity Extraction using medspaCy and scispaCy
Extracts Past Medical History, Medications, Vitals, and other clinical entities
Uses pre-trained models and pattern matching for comprehensive coverage
"""
import medspacy
import spacy
from medspacy.ner import TargetRule
from medspacy.context import ConTextRule
from typing import Dict, List
import re

# Load scispaCy model for better medical entity recognition
try:
    # Load scispaCy model first
    nlp_sci = spacy.load("en_core_sci_sm")
    # Create a new medspaCy pipeline with the scispaCy model as base
    nlp = medspacy.load(model="en_core_sci_sm", enable=["tok2vec", "tagger", "parser", "ner"])
except OSError:
    # Fallback to default medspaCy model if scispaCy not available
    print("scispaCy model not found, using default medspaCy model")
    nlp = medspacy.load()

# Add pattern-based medication extraction
def extract_medications_by_patterns(text: str) -> List[str]:
    """
    Extract medications using comprehensive patterns instead of hardcoded lists
    """
    medications = []
    
    # Common medication patterns
    med_patterns = [
        # Medication with dosage (most reliable)
        r'\b([A-Z][a-z]+(?:in|ol|pril|statin|mycin|cillin))\s+\d+\s*mg\b',
        # Medications in lists after common prefixes
        r'(?:take|taking|prescribed|on)\s+([A-Z][a-z]+)\b',
        # Medications followed by dosage
        r'\b([A-Z][a-z]{3,})\s+\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|units?)\b',
    ]
    
    for pattern in med_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            med = match.group(1).strip()
            if len(med) > 3 and med.lower() not in ['take', 'taking', 'with', 'current', 'continue']:
                medications.append(med)
    
    return medications

def extract_conditions_by_patterns(text: str) -> List[str]:
    """
    Extract medical conditions using patterns and medical terminology
    """
    conditions = []
    
    # Common condition patterns (more specific)
    condition_patterns = [
        # Conditions ending with medical suffixes
        r'\b([A-Z][a-z]+(?:itis|osis|emia|pathy|trophy|plasia|galy|oma|cardia|pnea))\b',
        # Disease/syndrome patterns
        r'\b([A-Z][a-z]+\s+(?:disease|syndrome|disorder|condition))\b',
        # Type X diabetes pattern
        r'\b(Type\s+\d+\s+diabetes(?:\s+mellitus)?)\b',
    ]
    
    for pattern in condition_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            condition = match.group(1).strip()
            if len(condition) > 4:
                conditions.append(condition)
    
    return conditions
# Enhanced target rules focusing on section headers and key phrases
target_rules = [
    # Section-based patterns
    TargetRule("past medical history", "SECTION_PMH"),
    TargetRule("medical history", "SECTION_PMH"),
    TargetRule("pmh", "SECTION_PMH"),
    TargetRule("medications", "SECTION_MEDS"),
    TargetRule("current medications", "SECTION_MEDS"),
    TargetRule("meds", "SECTION_MEDS"),
    TargetRule("vitals", "SECTION_VITALS"),
    TargetRule("vital signs", "SECTION_VITALS"),
    
    # High-confidence specific terms
    TargetRule("blood pressure", "VITALS"),
    TargetRule("heart rate", "VITALS"),
    TargetRule("temperature", "VITALS"),
    TargetRule("respiratory rate", "VITALS"),
    TargetRule("oxygen saturation", "VITALS"),
    
    # Common symptoms that are easily identifiable
    TargetRule("chest pain", "SYMPTOM"),
    TargetRule("shortness of breath", "SYMPTOM"),
    TargetRule("difficulty breathing", "SYMPTOM"),
]

# Check if components are already in pipeline before adding
try:
    if "medspacy_target_matcher" not in nlp.pipe_names:
        nlp.add_pipe("medspacy_target_matcher", config={"target_rules": target_rules})
    else:
        # Get existing target matcher and add new rules
        target_matcher = nlp.get_pipe("medspacy_target_matcher")
        target_matcher.add(target_rules)

    if "medspacy_context" not in nlp.pipe_names:
        nlp.add_pipe("medspacy_context")
except Exception as e:
    print(f"Warning: Could not add medspaCy components: {e}")
    # Continue with basic spaCy model
    pass

def extract_vitals_with_values(text: str) -> List[Dict]:
    """Extract vitals with their numerical values"""
    vitals_patterns = {
        "blood_pressure": r"(?:bp|blood pressure|b\.p\.?)\s*:?\s*(\d{2,3})/(\d{2,3})",
        "heart_rate": r"(?:hr|heart rate|pulse)\s*:?\s*(\d{2,3})\s*(?:bpm|beats)",
        "temperature": r"(?:temp|temperature|t)\s*:?\s*(\d{2,3}(?:\.\d)?)\s*(?:°f|f|fahrenheit|°c|c|celsius)",
        "respiratory_rate": r"(?:rr|respiratory rate|resp)\s*:?\s*(\d{1,2})",
        "oxygen_saturation": r"(?:o2 sat|oxygen saturation|spo2|sat)\s*:?\s*(\d{2,3})%?",
        "weight": r"(?:weight|wt)\s*:?\s*(\d{1,3}(?:\.\d)?)\s*(?:lbs|kg|pounds)",
        "height": r"(?:height|ht)\s*:?\s*(\d{1,2})'?\s*(\d{1,2})?\"?|(\d{1,3})\s*(?:cm|inches)",
    }
    
    vitals = []
    for vital_type, pattern in vitals_patterns.items():
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            if vital_type == "blood_pressure":
                vitals.append({
                    "type": "blood_pressure",
                    "systolic": match.group(1),
                    "diastolic": match.group(2),
                    "text": match.group(0)
                })
            elif vital_type == "height" and len(match.groups()) > 2:
                vitals.append({
                    "type": "height",
                    "value": match.group(3) if match.group(3) else f"{match.group(1)}'{match.group(2)}\"",
                    "text": match.group(0)
                })
            else:
                vitals.append({
                    "type": vital_type,
                    "value": match.group(1),
                    "text": match.group(0)
                })
    
    return vitals

def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    Extract clinical entities from medical text using multiple approaches:
    1. scispaCy pre-trained models (if available)
    2. medspaCy context-aware extraction (if available)
    3. Pattern-based extraction for comprehensive coverage
    """
    entities = {
        "past_medical_history": [],
        "medications": [],
        "vitals": [],
        "symptoms": [],
        "plan": [],
        "vitals_with_values": [],
        "all_entities": []  # All entities found by NLP models
    }
    
    try:
        doc = nlp(text)
        
        # Extract all entities using the loaded model
        for ent in doc.ents:
            entities["all_entities"].append({
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char
            })
            
            # Categorize based on entity labels (works for both scispaCy and medspaCy)
            if ent.label_ in ["CHEMICAL", "DRUG"]:
                entities["medications"].append(ent.text)
            elif ent.label_ in ["DISEASE", "DISORDER", "INJURY_OR_POISONING"]:
                entities["past_medical_history"].append(ent.text)
            elif ent.label_ in ["SIGN_OR_SYMPTOM"]:
                entities["symptoms"].append(ent.text)
            elif ent.label_ == "VITALS":
                entities["vitals"].append(ent.text)
            elif ent.label_ == "SYMPTOM" and hasattr(ent, '_') and hasattr(ent._, 'is_negated') and not ent._.is_negated:
                entities["symptoms"].append(ent.text)
    
    except Exception as e:
        print(f"Warning: NLP processing failed: {e}")
        # Continue with pattern-based extraction only
    
    # Pattern-based extraction for better coverage (always runs)
    pattern_medications = extract_medications_by_patterns(text)
    entities["medications"].extend(pattern_medications)
    
    pattern_conditions = extract_conditions_by_patterns(text)
    entities["past_medical_history"].extend(pattern_conditions)
    
    # Extract vitals with numerical values
    entities["vitals_with_values"] = extract_vitals_with_values(text)
    
    # Extract medications and conditions from specific sections
    section_based_entities = extract_from_sections(text)
    for key, values in section_based_entities.items():
        if key in entities:
            entities[key].extend(values)
    
    # Section-based extraction for structured sections (only once)
    sections = extract_by_sections(text)
    if sections:
        # Only add sections that don't already exist in entities
        for section_key, section_values in sections.items():
            if section_key not in entities:
                entities[section_key] = section_values
    
    # Clean up and remove duplicates
    for key in entities:
        if key not in ["vitals_with_values", "all_entities"]:
            # Remove duplicates while preserving order
            entities[key] = list(dict.fromkeys(entities[key]))
            # Filter out very short, common words, and formatting artifacts
            entities[key] = [item.strip() for item in entities[key] 
                           if len(item.strip()) > 2 and 
                           item.lower().strip() not in ['the', 'and', 'for', 'with', 'mg', 'ml', 'daily', 'twice', 'current', 'pain', 'obtain'] and
                           not item.strip().startswith('-') and
                           not item.strip().startswith('•') and
                           not item.strip().isdigit()]
            # Remove empty strings
            entities[key] = [item for item in entities[key] if item.strip()]
    
    return entities

def extract_from_sections(text: str) -> Dict[str, List[str]]:
    """
    Extract medications and conditions from specific sections of medical notes
    """
    entities = {
        "medications": [],
        "past_medical_history": []
    }
    
    # Define section patterns
    med_section_pattern = r'(?:medications?|meds|current medications?):\s*(.*?)(?=\n[A-Z][^:]*:|$)'
    pmh_section_pattern = r'(?:past medical history|pmh|medical history):\s*(.*?)(?=\n[A-Z][^:]*:|$)'
    
    # Extract from medication sections
    med_matches = re.finditer(med_section_pattern, text, re.IGNORECASE | re.DOTALL)
    for match in med_matches:
        section_text = match.group(1)
        meds = extract_medications_by_patterns(section_text)
        entities["medications"].extend(meds)
        
        # Also extract line by line for medications
        lines = section_text.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('-') and len(line) > 3:
                # Clean up common list markers
                line = re.sub(r'^[\d\.\-\*\+]\s*', '', line)
                if line:
                    entities["medications"].append(line)
    
    # Extract from PMH sections
    pmh_matches = re.finditer(pmh_section_pattern, text, re.IGNORECASE | re.DOTALL)
    for match in pmh_matches:
        section_text = match.group(1)
        conditions = extract_conditions_by_patterns(section_text)
        entities["past_medical_history"].extend(conditions)
        
        # Also extract line by line for conditions
        lines = section_text.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('-') and len(line) > 3:
                # Clean up common list markers
                line = re.sub(r'^[\d\.\-\*\+]\s*', '', line)
                if line:
                    entities["past_medical_history"].append(line)
    
    return entities

def extract_by_sections(text: str) -> Dict[str, List[str]]:
    """
    Extract entities based on common medical note sections
    """
    sections = {
        "chief_complaint": [],
        "history_of_present_illness": [],
        "review_of_systems": [],
        "physical_exam": [],
        "assessment_and_plan": []
    }
    
    # Common section headers patterns
    section_patterns = {
        "chief_complaint": r"(?:chief complaint|cc):\s*(.*?)(?=\n(?:[A-Z][^:]*:|$))",
        "history_of_present_illness": r"(?:history of present illness|hpi):\s*(.*?)(?=\n(?:[A-Z][^:]*:|$))",
        "review_of_systems": r"(?:review of systems|ros):\s*(.*?)(?=\n(?:[A-Z][^:]*:|$))",
        "physical_exam": r"(?:physical exam|pe|examination):\s*(.*?)(?=\n(?:[A-Z][^:]*:|$))",
        "assessment_and_plan": r"(?:assessment and plan|a&p|plan):\s*(.*?)(?=\n(?:[A-Z][^:]*:|$))"
    }
    
    for section, pattern in section_patterns.items():
        matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
        for match in matches:
            content = match.group(1).strip()
            if content:
                sections[section].append(content)
    
    return sections
