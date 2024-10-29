import uuid

def react_bundle_url(name):
    return f'http://localhost:8080/{name}.dev.js?cachebust={uuid.uuid4()}'

def css_url():
    return f'http://localhost:8080/style.dev.css?cachebust={uuid.uuid4()}'

