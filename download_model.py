# download_model.py
from huggingface_hub import snapshot_download
import os

# Настройки
model_name = "sentence-transformers/all-MiniLM-L6-v2"
local_dir = "models/all-MiniLM-L6-v2"

print(f"🚀 Начинаю загрузку модели: {model_name}")
print(f"📁 Модель будет сохранена в: {os.path.abspath(local_dir)}")

# Создаём папку, если её нет
os.makedirs(local_dir, exist_ok=True)

# Скачиваем модель
try:
    snapshot_download(
        repo_id=model_name,
        local_dir=local_dir,
        local_dir_use_symlinks=False  # безопасно для Windows
    )
    print(f"✅ Успешно: модель сохранена в {local_dir}")
    print("Теперь в коде используй: model_name = './models/all-MiniLM-L6-v2'")
except Exception as e:
    print(f"❌ Ошибка при загрузке модели: {e}")