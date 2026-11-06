import json

from fastapi.testclient import TestClient

from app.api import main


class FakeRedis:
    def __init__(self, values=None):
        self.values = dict(values or {})

    def get(self, key):
        return self.values.get(key)

    def setex(self, key, ttl, value):
        self.values[key] = value
        self.last_ttl = ttl


class FakeElasticsearch:
    def __init__(self):
        self.search_calls = []

    def search(self, **kwargs):
        self.search_calls.append(kwargs)
        if kwargs.get("aggs"):
            return {
                "aggregations": {
                    "courses": {
                        "buckets": [{"key": "Sistemas de Informação", "doc_count": 2}]
                    }
                }
            }
        return {
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_id": "question-1",
                        "_score": 1.0,
                        "_source": {
                            "statement": "Questão sobre ética e tecnologia",
                            "answer_key": "A",
                        },
                        "highlight": {"statement": ["Questão sobre <em>ética</em>"]},
                    }
                ],
            }
        }


def make_client(monkeypatch):
    redis = FakeRedis(
        {
            "token:student": json.dumps({"username": "student", "role": "ESTUDANTE"}),
            "token:teacher": json.dumps({"username": "teacher", "role": "PROFESSOR"}),
        }
    )
    elasticsearch = FakeElasticsearch()
    monkeypatch.setattr(main, "redis", redis)
    monkeypatch.setattr(main, "es", elasticsearch)
    return TestClient(main.app), redis, elasticsearch


def test_student_search_hides_answer_and_reuses_cache(monkeypatch):
    client, redis, elasticsearch = make_client(monkeypatch)
    headers = {"Authorization": "Bearer student"}

    first = client.get("/questions?q=ética", headers=headers)
    second = client.get("/questions?q=ética", headers=headers)

    assert first.status_code == 200
    assert "answer_key" not in first.json()["items"][0]["question"]
    assert second.json() == first.json()
    assert len(elasticsearch.search_calls) == 1
    assert redis.last_ttl == 60


def test_teacher_search_includes_answer_and_can_view_analytics(monkeypatch):
    client, _, elasticsearch = make_client(monkeypatch)
    headers = {"Authorization": "Bearer teacher"}

    search = client.get("/questions?q=ética", headers=headers)
    analytics = client.get("/analytics/courses", headers=headers)

    assert search.status_code == 200
    assert search.json()["items"][0]["question"]["answer_key"] == "A"
    assert analytics.status_code == 200
    assert analytics.json()[0]["course"] == "Sistemas de Informação"
    assert len(elasticsearch.search_calls) == 2


def test_student_cannot_view_analytics(monkeypatch):
    client, _, _ = make_client(monkeypatch)

    response = client.get(
        "/analytics/courses",
        headers={"Authorization": "Bearer student"},
    )

    assert response.status_code == 403


def test_search_accepts_multiple_areas(monkeypatch):
    client, _, elasticsearch = make_client(monkeypatch)

    response = client.get(
        "/questions?q=saúde&area=Saúde&area=Computação",
    )

    assert response.status_code == 200
    filters = elasticsearch.search_calls[0]["body"]["query"]["bool"]["filter"]
    assert {"terms": {"area": ["Saúde", "Computação"]}} in filters


def test_login_issues_non_deterministic_session_tokens(monkeypatch):
    client, redis, _ = make_client(monkeypatch)
    monkeypatch.setattr(
        main,
        "authenticate_ldap",
        lambda username, password: {"username": username, "role": "ESTUDANTE"},
    )

    first = client.post(
        "/auth/login",
        json={"username": "student", "password": "password"},
    )
    second = client.post(
        "/auth/login",
        json={"username": "student", "password": "password"},
    )

    first_token = first.json()["access_token"]
    second_token = second.json()["access_token"]
    assert first.status_code == second.status_code == 200
    assert first_token != second_token
    assert json.loads(redis.get(f"token:{first_token}"))["role"] == "ESTUDANTE"
