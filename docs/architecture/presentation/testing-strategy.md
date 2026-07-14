# Design: Testing Strategy

**Epic**: 6 — Presentation Layer & External Adapters Design
**Version**: 1.0

---

## 1. Testing Pyramid

```
         ╱╲
        ╱  ╲         Performance Tests (1-2)
       ╱    ╲        Manual + k6/locust
      ╱──────╲
     ╱        ╲      Contract Tests (5-10)
    ╱          ╲     OpenAPI schema validation
   ╱────────────╲
  ╱              ╲   Integration Tests (20-30)
 ╱                ╲  TestClient + InMemory UoW
╱──────────────────╲
╱                    ╲ Unit Tests (80-120)
╱──────────────────────╲  Mock services, model validation
```

## 2. Unit Tests

### Pydantic Model Validation

```python
# tests/ingestion/presentation/models/test_source_requests.py
def test_create_source_request_valid():
    req = CreateSourceRequest(name="Tech", source_type="RSS", source_url="https://example.com/feed")
    assert req.name == "Tech"

def test_create_source_request_empty_name():
    with pytest.raises(ValidationError):
        CreateSourceRequest(name="", source_type="RSS", source_url="https://example.com/feed")

def test_create_source_request_invalid_url():
    with pytest.raises(ValidationError):
        CreateSourceRequest(name="Tech", source_type="RSS", source_url="not-a-url")
```

### Error Mapper Tests

```python
# tests/ingestion/presentation/exceptions/test_error_mapper.py
def test_not_found_error_returns_404():
    error = Error(code=ApplicationErrorCode.RESOURCE_NOT_FOUND, message="not found")
    status = map_error_to_http_status(error)
    assert status == 404

def test_duplicate_error_returns_409():
    error = Error(code=IngestionErrorCode.DUPLICATE_NEWS_SOURCE, message="duplicate")
    status = map_domain_error_to_http_status(error)
    assert status == 409
```

### Problem Details Tests

```python
def test_problem_detail_serialization():
    pd = ProblemDetail(title="Not Found", status=404, detail="Source not found")
    data = pd.model_dump()
    assert data["status"] == 404
    assert "title" in data
```

## 3. API Tests (TestClient)

```python
# tests/ingestion/presentation/api/test_sources.py
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    app = create_app()
    app.dependency_overrides[get_uow] = lambda: InMemoryUnitOfWork()
    return TestClient(app)

def test_register_source_success(client):
    response = client.post("/api/v1/sources", json={
        "name": "TechCrunch",
        "source_type": "RSS",
        "source_url": "https://techcrunch.com/feed/",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["name"] == "TechCrunch"
    assert "id" in data["data"]

def test_register_source_duplicate_name(client):
    client.post("/api/v1/sources", json={
        "name": "TechCrunch", "source_type": "RSS", "source_url": "https://example.com",
    })
    response = client.post("/api/v1/sources", json={
        "name": "TechCrunch", "source_type": "RSS", "source_url": "https://example2.com",
    })
    assert response.status_code == 409

def test_get_source_not_found(client):
    response = client.get("/api/v1/sources/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404

def test_list_active_sources(client):
    response = client.get("/api/v1/sources")
    assert response.status_code == 200
    assert "data" in response.json()

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] in ("healthy", "degraded")
```

## 4. Integration Tests

Full stack with InMemory repositories:

```python
# tests/ingestion/presentation/integration/test_source_flow.py
def test_full_source_lifecycle(client):
    # Create
    create_resp = client.post("/api/v1/sources", json={...})
    source_id = create_resp.json()["data"]["id"]

    # Find
    find_resp = client.get(f"/api/v1/sources/{source_id}")
    assert find_resp.json()["data"]["id"] == source_id

    # Update
    update_resp = client.put(f"/api/v1/sources/{source_id}", json={"name": "Updated"})
    assert update_resp.json()["data"]["name"] == "Updated"

    # Activate
    activate_resp = client.post(f"/api/v1/sources/{source_id}/activate")
    assert activate_resp.json()["data"]["is_active"] == True
```

## 5. Contract Tests

Validate OpenAPI schema is consistent:

```python
# tests/ingestion/presentation/contract/test_openapi.py
def test_openapi_schema_valid(client):
    response = client.get("/openapi.json")
    schema = response.json()
    assert "openapi" in schema
    assert "paths" in schema
    assert "/api/v1/sources" in schema["paths"]
```

## 6. Test Fixtures

```python
# tests/ingestion/presentation/conftest.py
@pytest.fixture
def in_memory_uow():
    return InMemoryUnitOfWork()

@pytest.fixture
def client(in_memory_uow):
    app = create_app()
    app.dependency_overrides[get_uow] = lambda: in_memory_uow
    return TestClient(app)

@pytest.fixture
def sample_source():
    return {
        "name": "Test Source",
        "source_type": "RSS",
        "source_url": "https://example.com/feed",
    }
```

## 7. Coverage Targets

| Layer | Target | Scope |
|-------|--------|-------|
| Unit (models) | 95% | Pydantic validation, error mapping |
| Unit (middleware) | 90% | Request ID, correlation, timing |
| API | 85% | All 27 endpoints happy + error paths |
| Integration | 70% | Full lifecycle flows |
| Contract | 100% | OpenAPI schema validation |

---

*See also: `api-design.md`, `exception-handling.md`*
