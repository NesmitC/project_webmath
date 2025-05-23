from neuroassist.assistant import CompanyAssistant

assistant = CompanyAssistant()
response = assistant.find_answer("Как интегрировать x^2?")
print(response)