# test_assistant.py

from neuroassist.assistant import CompanyAssistant

assistant = CompanyAssistant()
response = assistant.find_answer("расскажи про задание 13")
print(response)