with open("scripts/test_acceptance.py", "r") as f:
    content = f.read()

content = content.replace(
    '            r = await client.post(\n                "http://127.0.0.1:8000/v1/chat/completions",\n                json={\n                    "model": "gpt-4o",\n                    "messages": [\n                        {"role": "user", "content": "Hello, world!"}\n                    ]\n                }\n            )',
    '            r = await client.post(\n                "http://127.0.0.1:8000/v1/chat/completions",\n                json={\n                    "model": "gpt-4o",\n                    "messages": [\n                        {"role": "user", "content": "Hello, world!"}\n                    ]\n                }\n            )' # didn't change anything, going manual
)
