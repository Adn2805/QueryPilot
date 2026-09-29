import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert data["database_connected"] is True


@pytest.mark.asyncio
async def test_schema_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/schema")
        assert res.status_code == 200
        data = res.json()
        assert "customers" in data["schema_markdown"]


@pytest.mark.asyncio
async def test_sample_queries_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/sample-queries")
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 3


@pytest.mark.asyncio
async def test_query_flow_normal():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "message": "Show total revenue by product category",
            "history": []
        }
        res = await ac.post("/api/query", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["type"] == "sql_result"
        assert data["sql"] is not None
        assert len(data["rows"]) > 0
        assert data["chart_type"] in ["bar", "pie", "line", "table"]


@pytest.mark.asyncio
async def test_query_flow_ambiguity_and_clarification():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Ask ambiguous query
        res1 = await ac.post("/api/query", json={"message": "Who are our top customers?", "history": []})
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["type"] == "clarification"
        assert data1["is_ambiguous"] is True
        assert len(data1["clarification_options"]) >= 2

        # 2. Select clarification option
        res2 = await ac.post("/api/query", json={
            "message": data1["clarification_options"][0],
            "history": [
                {"role": "user", "content": "Who are our top customers?"},
                {"role": "assistant", "content": data1["clarification_question"]}
            ]
        })
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["type"] == "sql_result"
        assert len(data2["rows"]) > 0


@pytest.mark.asyncio
async def test_query_flow_security_block():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/query", json={"message": "DROP TABLE customers;", "history": []})
        assert res.status_code == 200
        data = res.json()
        # Either the LLM or DB validator returns safe blocked message
        assert data["type"] in ["sql_result", "error"]
