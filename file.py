with open('data.json', 'rb') as f:
    content = f.read()

# Re-encode the content into UTF-8
with open('data_utf8.json', 'w', encoding='utf-8') as f:
    f.write(content.decode('utf-8', 'ignore'))