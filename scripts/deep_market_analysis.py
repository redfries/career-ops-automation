import sqlite3, re, json
from collections import Counter

conn = sqlite3.connect('data/jobs.db')
cur = conn.cursor()

cur.execute("SELECT id, title, company, location, source, description_text, status FROM jobs")
rows = cur.fetchall()
total_jobs = len(rows)

print(f"Total Unique Jobs Analyzed: {total_jobs}")

# 1. Sources breakdown
source_counts = Counter(r[4] for r in rows)
print("\n--- Breakdown by Portal ---")
for s, c in source_counts.most_common():
    print(f"{s.upper()}: {c} ({c/total_jobs*100:.1f}%)")

# 2. Location breakdown
def clean_loc(loc, status):
    if status == 'out_of_region':
        return 'United States (Out of Region / No Visa Auth)'
    loc_lower = (loc or '').lower()
    if 'riyadh' in loc_lower or 'الرياض' in loc_lower:
        return 'Riyadh, Saudi Arabia'
    elif 'dammam' in loc_lower or 'khobar' in loc_lower or 'dhahran' in loc_lower or 'eastern' in loc_lower:
        return 'Eastern Province (Dhahran/Khobar/Dammam)'
    elif 'jeddah' in loc_lower or 'جدة' in loc_lower or 'mecca' in loc_lower or 'medina' in loc_lower or 'makkah' in loc_lower:
        return 'Western Province (Jeddah/Mecca)'
    elif 'dubai' in loc_lower or 'abu dhabi' in loc_lower or 'sharjah' in loc_lower or 'uae' in loc_lower or 'united arab emirates' in loc_lower:
        return 'UAE (Dubai / Abu Dhabi)'
    elif 'remote' in loc_lower:
        return 'Remote (Global/Contractor)'
    elif 'saudi' in loc_lower or 'ksa' in loc_lower:
        return 'Saudi Arabia (General / Multiple Cities)'
    else:
        return 'Other Regional / Unspecified'

loc_counter = Counter(clean_loc(r[3], r[6]) for r in rows)
print("\n--- Geographic Distribution ---")
for l, c in loc_counter.most_common():
    print(f"{l}: {c} ({c/total_jobs*100:.1f}%)")

# 3. Top Tech Stacks across ALL descriptions & titles
tech_keywords = {
    # Core Languages
    'Python': r'\bpython\b',
    'SQL': r'\bsql\b',
    'C++': r'\bc\+\+\b',
    'R': r'\b(r|r-project|cran)\b',
    'Java/Scala': r'\b(java|scala)\b',
    
    # ML & Deep Learning
    'PyTorch': r'\bpytorch\b',
    'TensorFlow / Keras': r'\b(tensorflow|keras)\b',
    'Scikit-Learn': r'\b(scikit-learn|sklearn)\b',
    'Computer Vision (OpenCV/YOLO)': r'\b(computer vision|opencv|yolo|object detection|image processing)\b',
    'NLP / Text Processing': r'\b(nlp|natural language processing|tokeniz|spacy|nltk)\b',
    'Deep Learning (General)': r'\b(deep learning|neural networks|cnn|transformer)\b',
    
    # GenAI & Modern 2026 Tech
    'LLMs / Generative AI': r'\b(llm|llms|large language model|generative ai|genai|gpt|claude|gemini|mistral|llama)\b',
    'RAG (Retrieval-Augmented Generation)': r'\b(rag|retrieval-augmented|retrieval augmented|vector db|vector database|chroma|pinecone|weaviate|qdrant|faiss)\b',
    'Agentic AI / Orchestration': r'\b(agent|agentic|langchain|langgraph|llamaindex|crewai|autogen)\b',
    'Prompt Engineering': r'\b(prompt engineering|fine-tuning|finetuning|lora|peft)\b',
    
    # MLOps, Data & Cloud
    'Cloud (AWS/Azure/GCP)': r'\b(aws|azure|gcp|google cloud|cloud)\b',
    'Docker / Containers': r'\b(docker|container|kubernetes|k8s)\b',
    'MLOps / Pipelines': r'\b(mlops|kubeflow|mlflow|ci/cd|pipeline|airflow)\b',
    'Big Data (Spark/Databricks/Hadoop)': r'\b(spark|pyspark|databricks|hadoop)\b',
    'Data Analytics / BI (PowerBI/Tableau)': r'\b(power bi|powerbi|tableau|excel|analytics|dashboard)\b'
}

tech_stats = {k: 0 for k in tech_keywords}

for r in rows:
    text = f"{r[1]} {r[5]}".lower()
    for tech, pattern in tech_keywords.items():
        if re.search(pattern, text):
            tech_stats[tech] += 1

print(f"\n--- Empirical Tech Stack Demand (Out of {total_jobs} jobs) ---")
sorted_tech = sorted(tech_stats.items(), key=lambda x: x[1], reverse=True)
for tech, count in sorted_tech:
    print(f"{tech}: {count} ({count/total_jobs*100:.1f}%)")

# 4. Job Role Archetypes
role_categories = {
    'Machine Learning / Deep Learning Engineer': r'\b(machine learning|deep learning|ml engineer|mle)\b',
    'AI Engineer / GenAI Specialist': r'\b(ai engineer|artificial intelligence engineer|generative ai|genai|prompt engineer|llm engineer)\b',
    'Data Scientist': r'\b(data scientist|data science)\b',
    'Computer Vision Engineer': r'\b(computer vision|vision|image processing)\b',
    'NLP / Conversational AI Engineer': r'\b(nlp|natural language|speech|conversational)\b',
    'Data Analyst / BI Specialist': r'\b(data analyst|business analyst|bi analyst|intelligence analyst)\b',
    'AI / Data Intern or Graduate Trainee': r'\b(intern|internship|graduate|trainee|fresher|fellow)\b'
}

role_stats = {k: 0 for k in role_categories}
for r in rows:
    title = r[1].lower()
    for role, pattern in role_categories.items():
        if re.search(pattern, title):
            role_stats[role] += 1

print("\n--- Role Archetypes Breakdown ---")
for role, count in sorted(role_stats.items(), key=lambda x: x[1], reverse=True):
    print(f"{role}: {count} ({count/total_jobs*100:.1f}%)")

# Output JSON summary for artifact reporting
report_data = {
    'total_jobs': total_jobs,
    'source_breakdown': dict(source_counts),
    'geo_breakdown': dict(loc_counter),
    'tech_demand': sorted_tech,
    'role_breakdown': sorted(role_stats.items(), key=lambda x: x[1], reverse=True)
}

with open('data/combined_analysis_summary.json', 'w', encoding='utf-8') as f:
    json.dump(report_data, f, indent=2)

print("\nAnalysis written to data/combined_analysis_summary.json")
conn.close()
