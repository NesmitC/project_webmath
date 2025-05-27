from rag import KnowledgeSearch

kb = KnowledgeSearch("data/rus/ege.txt")

# Точный запрос по заданию 13
result = kb.search("Какие слова с НЕ пишутся слитно?")
print(result)