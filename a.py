# 需要安装: pip install google-generativeai
import google.generativeai as genai

# 使用 Antigravity 代理地址 (推荐 127.0.0.1)
genai.configure(
    api_key="sk-50c3d8d9d6884dafa9b1e17ebff450d7",
    transport='rest',
    client_options={'api_endpoint': 'http://127.0.0.1:8045'}
)

model = genai.GenerativeModel('gemini-3-flash')
response = model.generate_content("Hello")
print(response.text)