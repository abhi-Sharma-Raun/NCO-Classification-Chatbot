import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
from tqdm import tqdm

df9=pd.read_csv(r".\EmbeddingsV-0.2.csv")  # CDownload the dataset and add it in the current project folder
def get_metadata(df_row):
    '''Make the metadata for the embeddings having code, family_name, division_name, title'''
    
    return {
        "occupation_code": df_row['code'],
        "family_name": df_row['family_name'],
        "division_name": df_row['division_name'],
        "occupation_title": df_row['title']
    }
documents=df9['final_title'].to_list()
metadatas=df9.apply(get_metadata, axis=1).to_list()
ids=df9['code'].astype(str).to_list()

client=chromadb.PersistentClient("./embeddings")
default_ef=embedding_functions.DefaultEmbeddingFunction()
collection=client.create_collection(name="EmbeddingsV-0.2_all-MiniLM-L6-v2", embedding_function=default_ef)

def batch_add(collection, documents, metadatas, ids, batch_size=500):
    total_docs=len(documents)
    for i in tqdm(range(0, total_docs, batch_size)):
        batch_docs=documents[i:i+batch_size]
        batch_meta=metadatas[i:i+batch_size]
        batch_ids=ids[i:i+batch_size]

        collection.add(
            documents=batch_docs,
            metadatas=batch_meta,
            ids=batch_ids
        )
    print("added documents")
    
if collection.count() == 0:
    batch_add(collection, documents, metadatas, ids)
else:
    print(f"Collection already contains {collection.count()} documents.")