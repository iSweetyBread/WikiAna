import requests
import json

# url = 'https://en.wikipedia.org/w/rest.php/v1/page/Agapanthus/history'
# headers = {'User-Agent': 'CoolBot/0.0 (https://example.org/coolbot/; coolbot@example.org)'}

# data = []

# while True:
#     response = requests.get(url=url, headers=headers)
#     response_data = json.loads(response.text)
    
#     data.append(response_data)
    
#     try:
#         url = response_data['older']
#         print(url)
#     except:
#         break

# with open('data.json', 'w', encoding='utf-8') as f:
#     json.dump(data, f, ensure_ascii=False, indent=4)

aaa = {
    '1': 1,
    '2': 2,
    '3': 3
}
aaa1 = {
    '1': 1,
    '2': 2,
    '3': 3
}
aaa2 = {
    '1': [1, 2],
    '2': 2,
    '3': 4
}
b = list({frozenset(d.items()) for d in [aaa, aaa1, aaa2]})
b = [dict(f) for f in b]
print(b)