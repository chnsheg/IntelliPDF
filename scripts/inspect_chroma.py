from app.infrastructure.vector_db.client import get_chroma_client, get_collection

c = get_chroma_client()
print('client ok')
cols = c.list_collections()
print('collections', cols)
col = get_collection()
print('collection name', col.name)
try:
    stats = col.count()
    print('count', stats)
    res = col.get(limit=5)
    print('sample ids', res.get('ids'))
except Exception as e:
    print('error', e)
