import requests


def test_ollama_can_generate():
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "gemma4:e2b",
            "prompt": "Hello",
            "stream": False,
        },
        timeout=200,
    )

    assert response.status_code == 200
    assert "response" in response.json()
