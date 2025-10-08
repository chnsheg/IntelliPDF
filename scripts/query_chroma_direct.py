from app.infrastructure.vector_db.client import get_chroma_client
from app.services.ai.embeddings import EmbeddingsService
from app.core.config import get_settings

settings = get_settings()
client = get_chroma_client()
collection = client.get_collection(name=settings.chroma_collection_name)

DOC_ID = '8523c731-ccea-4137-8472-600dcb5f4b64'
query = '什么是本文件的主要主题？'

emb = EmbeddingsService()
qe = emb.encode_text(query, show_progress=False)
print('query vector len', len(qe))
print('first 5 elems', qe[:5])

res = collection.query(query_embeddings=[qe.tolist()], n_results=5, where={
                       'document_id': DOC_ID})
print('raw query result keys:', list(res.keys()))
for k, v in res.items():
    if isinstance(v, list) and len(v) > 0:
        print(k, 'len outer', len(v), 'len inner',
              len(v[0]) if v[0] is not None else 0)
    else:
        print(k, type(v))

print('ids sample:', res.get('ids'))
print('documents sample:', res.get('documents')[:3])
print('metadatas sample:', res.get('metadatas')[:3])
print('distances sample:', res.get('distances')[:3])
