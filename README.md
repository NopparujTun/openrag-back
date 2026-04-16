## Backend (FastAPI)

### Setup

Create a virtualenv, then:

```bash
pip install -r requirements.txt
copy .env.example .env
```

### Run

```bash
uvicorn app.main:app --reload --port 8000
```

