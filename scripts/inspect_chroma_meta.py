from app.infrastructure.vector_db.client import get_chroma_client
from app.core.config import get_settings

settings = get_settings()
client = get_chroma_client()
collection = client.get_collection(name=settings.chroma_collection_name)

DOC_ID = '8523c731-ccea-4137-8472-600dcb5f4b64'

print('collection count', collection.count())
res = collection.get(where={'document_id': DOC_ID}, limit=5)
print('keys:', list(res.keys()))
print('ids sample:', res.get('ids')[:5])
print('metadatas sample:', res.get('metadatas')[:5])
print('documents sample:', res.get('documents')[:5])
