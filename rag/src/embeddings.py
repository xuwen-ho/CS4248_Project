import json
import pandas as pd
import numpy as np
import os
from openai import OpenAI
import faiss

BATCH_SIZE = 100
MODEL = "text-embedding-3-small"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def load_scicite():
    scicite_sentences = []

    path_to_data = os.path.join('..', 'data', 'raw', 'test.jsonl')
    with open(path_to_data, "r", encoding='utf-8') as f:
        for line in f:
          scicite_sentences.append(json.loads(line))
    return pd.DataFrame(scicite_sentences)

def preprocess_sentence(df):
    # Extract only relevant fields, starting with citation sentences
    df['text_for_embeddings'] = "Claim: " + df['string'].fillna('')
    
    # Include section name and labels, if present
    if 'sectionName' in df.columns:
        df['text_for_embeddings'] += " Section Name: " + df['sectionName'].fillna('')
    if 'sectionName' in df.columns:
        df['text_for_embeddings'] += " Classification Label: " + df['label'].fillna('')

    return df

def generate_embeddings(df):

    all_embeddings = []
    client = OpenAI(api_key=OPENAI_API_KEY)

    for i in range(0, len(df), BATCH_SIZE):
        batch = df['text_for_embeddings'][i:i+BATCH_SIZE].tolist()
        
        try:
            response = client.embeddings.create(
                input=batch,
                model=MODEL
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

        except Exception as e:
            print("Error generating embeddings for batch {i}")

    embeddings = np.array(all_embeddings).astype('float32')
    # Store embeddings locally for future reference
    path_to_folder = os.path.join('..', 'data', 'embeddings')
    np.save(os.path.join(path_to_folder, 'test_embeddings.npy'), embeddings)
    
    return embeddings

def store_embeddings(embeddings):

    

    # Store embeddings into FAISS database
    # Create FAISS database and store embeddings
    dimension = embeddings.shape[1] 
    faiss_structure = faiss.IndexFlatL2(dimension)
    faiss_structure.add(embeddings)
    # Save FAISS database
    faiss.write_index(faiss_structure, os.path.join(os.path.join('..', 'data', 'embeddings'), 'faiss_index.idx'))

def run_pipeline():
    df = load_scicite()
    df = preprocess_sentence(df)
    df.to_csv(os.path.join(os.path.join('..', 'data', 'embeddings'), 'processed_data.csv'), index=False)
    # embeddings = generate_embeddings(df)
    # embeddings.type
    # embeddings[0]

    # path_to_data = os.path.join('..', 'data', 'embeddings', 'test_embeddings.npy')
    # embeddings = np.load(path_to_data)

    # store_embeddings(embeddings)

if __name__ == "__main__":
    run_pipeline()