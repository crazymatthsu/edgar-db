"""Tests for download endpoint (with mocked EdgarClient)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


class TestDownload:
    @patch("ui.backend.routes.download.get_config")
    @patch("ui.backend.routes.download.EdgarClient")
    @patch("ui.backend.routes.download.download_company")
    def test_download_success(
        self, mock_download: MagicMock, mock_client_cls: MagicMock,
        mock_config: MagicMock, client: TestClient,
    ) -> None:
        mock_download.return_value = 150
        mock_client_instance = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        resp = client.post("/api/download/AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ticker"] == "AAPL"
        assert data["status"] == "downloaded"
        assert data["facts_count"] == 150

    @patch("ui.backend.routes.download.get_config")
    @patch("ui.backend.routes.download.EdgarClient")
    @patch("ui.backend.routes.download.download_company")
    def test_download_already_current(
        self, mock_download: MagicMock, mock_client_cls: MagicMock,
        mock_config: MagicMock, client: TestClient,
    ) -> None:
        mock_download.return_value = 0
        mock_client_instance = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        resp = client.post("/api/download/AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "already_current"
        assert data["facts_count"] == 0

    @patch("ui.backend.routes.download.get_config")
    @patch("ui.backend.routes.download.EdgarClient")
    @patch("ui.backend.routes.download.download_company")
    def test_download_unknown_ticker_404(
        self, mock_download: MagicMock, mock_client_cls: MagicMock,
        mock_config: MagicMock, client: TestClient,
    ) -> None:
        mock_download.side_effect = ValueError("Unknown ticker: ZZZZ")
        mock_client_instance = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        resp = client.post("/api/download/ZZZZ")
        assert resp.status_code == 404

    @patch("ui.backend.routes.download.get_config")
    @patch("ui.backend.routes.download.EdgarClient")
    @patch("ui.backend.routes.download.download_company")
    def test_download_with_force(
        self, mock_download: MagicMock, mock_client_cls: MagicMock,
        mock_config: MagicMock, client: TestClient,
    ) -> None:
        mock_download.return_value = 200
        mock_client_instance = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        resp = client.post("/api/download/AAPL?force=true")
        assert resp.status_code == 200
        mock_download.assert_called_once()
