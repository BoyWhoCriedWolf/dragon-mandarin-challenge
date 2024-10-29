import uuid

def react_bundle_url(name):
    return f'http://194.87.110.41:8080/{name}.dev.js?cachebust={uuid.uuid4()}'

def css_url():
    return f'http://194.87.110.41:8080/style.dev.css?cachebust={uuid.uuid4()}'

