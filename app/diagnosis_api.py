import os
import re
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
def suggest_diagnosis(symptoms, conditions, medications):
    """
    Generates a structured diagnostic prompt for a language model using patient data.
    
    Parameters:
        symptoms (str): Description of current symptoms.
        conditions (str): Description of past or chronic medical conditions.
        medications (str): List or description of current medications.

    Returns:
        str: Formatted prompt for diagnostic generation.
    """

    prompt = f"""
Context:
The following patient data has been extracted:
- Symptoms: {symptoms}
- Previous Conditions: {conditions}
- Medications: {medications}

Based on this, generate a concise diagnostic summary.

Your task:
1. List the most likely diagnosis (or differential diagnoses if unclear)
2. Briefly explain reasoning based on symptoms and history
3. Indicate urgency (e.g., emergency, urgent care, routine)
4. Suggest next clinical steps (e.g., tests, referrals, treatment)

Tone: Keep it professional, brief, and free of generic AI language. Prioritize clarity over verbosity.

Output Format Example:

---
Likely Diagnosis: [Condition Name]  
Reasoning: [Short rationale]  
Urgency: [Emergency/Urgent/Routine]  
Next Steps: [Relevant tests/treatments/referrals]
---
"""
    
    openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=openrouter_api_key  # Explicitly pass the API key
    )
    try:
        completion = client.chat.completions.create(
            
            model="deepseek/deepseek-r1-distill-llama-70b:free",# i have used this model, might change to more specific model in next commit
            temperature=0.7,#kinda like creativity , i have set it to 0.7 might as well give user the authority
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        #MY CODE RETURNS ESCAPE CHAR SO I HAVE REMOVED IT MANUALLY
        return completion.choices[0].message.content.strip().replace("\\n", "\n")
    except Exception as e:
        return f"Diagnosis service error: {str(e)}"

def parse_diagnosis_response(response: str) -> dict:
    # Remove markdown bold if present
    response = response.replace("**", "")
    result = {}

    patterns = {
        "likely_diagnosis": r"Likely Diagnosis:\s*(.+?)(?:\s{2,}|$|\n)",
        "reasoning": r"Reasoning:\s*(.+?)(?:\s{2,}|$|\n)",
        "urgency": r"Urgency:\s*(.+?)(?:\s{2,}|$|\n)",
        "next_steps": r"Next Steps:\s*(.+?)(?:\s{2,}|$|\n)"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        result[key] = match.group(1).strip() if match else ""

    return result

# # TEST SAMPLE:
# response = """**Likely Diagnosis:** Asthma exacerbation  \n**Reasoning:** The patient's symptoms of shortness of breath, wheezing, and persistent dry cough, combined with a history of asthma and seasonal allergies, suggest an asthma flare-up. The use of albuterol indicates a known respiratory condition, and allergies could be exacerbating symptoms.  \n**Urgency:** Urgent care  \n**Next Steps:** Assess peak flow and spirometry, review and adjust asthma action plan, consider adding an inhaled corticosteroid, and ensure adherence to current medications. Referral to a pulmonologist if symptoms worsen or persist."""
# parsed = parse_diagnosis_response(response)
# print(parsed["likely_diagnosis"])  
# print(parsed["reasoning"])         
# print(parsed["urgency"])           
# print(parsed["next_steps"])
