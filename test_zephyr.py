from huggingface_hub import InferenceClient

client = InferenceClient(api_key='DEEPSEEK_API_KEY')

response = client.chat_completion(
    model="HuggingFaceH4/zephyr-7b-beta",
    messages=[{"role": "user", "content": "Как интегрировать x^2?"}]
)

print(response.choices[0].message.content)