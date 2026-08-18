from app import app

app.testing = True
client = app.test_client()
resp = client.get('/upload-resume')
print('STATUS', resp.status_code)
print(resp.get_data(as_text=True)[:1000])
