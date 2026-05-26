import pytest
from unittest.mock import patch, AsyncMock
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import Response

from app.main import app


@pytest.mark.asyncio
async def test_proxy_chat_completions_handler():
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello!"}]
    }

    with patch(
        "app.main.forward_and_log", new_callable=AsyncMock
    ) as mock_forward:
        mock_forward.return_value = Response(
            content='{"status": "ok"}', media_type="application/json"
        )

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            headers = {"Authorization": "Bearer test", "X-Custom": "Value"}
            response = await client.post(
                "/v1/chat/completions", json=payload, headers=headers
            )

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

        mock_forward.assert_called_once()

        kwargs = mock_forward.call_args.kwargs
        assert kwargs["payload"] == payload

        # Verify headers extraction (httpx lowercase them)
        assert kwargs["headers"]["authorization"] == "Bearer test"
        assert kwargs["headers"]["x-custom"] == "Value"

        # Verify db session
        assert isinstance(kwargs["db"], AsyncSession)
