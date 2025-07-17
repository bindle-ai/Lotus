import json
import pytest
from app import app, db, User

@pytest.fixture(autouse=True)
def run_around_tests(tmp_path):
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{tmp_path}/test.db'
    app.config['TESTING'] = True
    with app.app_context():
        db.create_all()
    yield
    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client():
    return app.test_client()

def test_register_and_confirm_and_login(client, capsys):
    resp = client.post('/register', json={'username': 'alice', 'email': 'alice@example.com', 'password': 'pass'})
    assert resp.status_code == 201
    captured = capsys.readouterr()
    # Extract token from printed confirmation link
    token_line = captured.out.strip().split('\n')[-1]
    token = token_line.rsplit('/', 1)[-1]

    resp = client.get(f'/confirm/{token}')
    assert resp.status_code == 200

    resp = client.post('/login', json={'username': 'alice', 'password': 'pass'})
    assert resp.status_code == 200
