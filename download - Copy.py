import requests, os

url = "https://huggingface.co/datasets/bitext/Bitext-customer-support-llm-chatbot-training-dataset/resolve/main/Bitext_Sample_Customer_Support_Training_Dataset_27K_responses-v11.csv"
out = "data.csv"

existing = os.path.getsize(out) if os.path.exists(out) else 0
headers = {"Range": f"bytes={existing}-"} if existing else {}

print(f"Starting from byte {existing}...")
with requests.get(url, headers=headers, stream=True, timeout=60) as r:
    mode = "ab" if existing else "wb"
    with open(out, mode) as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
print("Size now:", os.path.getsize(out), "bytes")
