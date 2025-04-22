from langchain_community.document_loaders import WebBaseLoader


page_url = "https://python.langchain.com/docs/how_to/chatbots_memory/"

loader = WebBaseLoader(web_paths=[page_url])
docs = []

for doc in loader.lazy_load():
    docs.append(doc)

assert len(docs) == 1
doc = docs[0]

print(doc)