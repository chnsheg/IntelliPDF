from app.services.ai.retrieval import RetrievalService

rs = RetrievalService()
res = rs.search_by_document(
    '什么是本文件的主要主题？', '8523c731-ccea-4137-8472-600dcb5f4b64', n_results=5)
print('result count', len(res))
for r in res[:5]:
    print(r['id'], r.get('metadata', {}).get('chunk_index'), r.get('distance'))
    print(r['text'][:200])
    print('---')
