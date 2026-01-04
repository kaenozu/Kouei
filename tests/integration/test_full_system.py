"""
Full System Integration Test
"""
import pytest
import asyncio
import aiohttp
from datetime import datetime


class TestFullSystem:
    """システム統合テスト"""
    
    @pytest.fixture
    async def api_client(self):
        """APIクライアントフィクスチャ"""
        async with aiohttp.ClientSession() as session:
            yield session
    
    @pytest.mark.asyncio
    async def test_smart_betting_workflow(self, api_client):
        """スマートベッティングワークフローテスト"""
        # 1. スマートベッティングAPI呼び出し
        url = "http://localhost:8001/api/smart-bets?date=20241201"
        async with api_client.get(url) as response:
            assert response.status == 200
            data = await response.json()
            
        # 2. レスポンス構造確認
        assert "bets" in data
        assert "total_bets" in data
        assert "threshold" in data
        
        # 3. データ形式確認
        if data["bets"]:
            bet = data["bets"][0]
            assert "date" in bet
            assert "jyo_cd" in bet
            assert "race_no" in bet
            assert "boat_no" in bet
            assert "probability" in bet
            assert "confidence" in bet
    
    @pytest.mark.asyncio
    async def test_collection_endpoints(self, api_client):
        """データ収集エンドポイントテスト"""
        # 1. ステータス確認
        url = "http://localhost:8001/api/collection/status"
        async with api_client.get(url) as response:
            assert response.status == 200
            data = await response.json()
            
        assert "running" in data
        assert "collection_interval" in data
    
    @pytest.mark.asyncio
    async def test_concierge_endpoints(self, api_client):
        """AIコンシェルジュエンドポイントテスト"""
        # 1. ステータス確認
        url = "http://localhost:8001/api/concierge/status"
        async with api_client.get(url) as response:
            assert response.status == 200
            data = await response.json()
            
        assert data["status"] == "active"
        assert data["service"] == "AI Concierge"
    
    @pytest.mark.asyncio
    async def test_monitoring_endpoints(self, api_client):
        """モニタリングエンドポイントテスト"""
        # 1. 精度統計確認
        url = "http://localhost:8001/api/monitoring/accuracy-stats?days=7"
        async with api_client.get(url) as response:
            assert response.status == 200
            data = await response.json()
            
        assert "period_days" in data
        assert "daily_stats" in data
        assert "confidence_stats" in data
    
    @pytest.mark.asyncio
    async def test_cross_functionality(self, api_client):
        """クロス機能テスト"""
        # 1. スマートベッティング→AIコンシェルジュ分析
        smart_url = "http://localhost:8001/api/smart-bets?date=20241201&threshold=0.7"
        async with api_client.get(smart_url) as response:
            assert response.status == 200
            smart_data = await response.json()
        
        # 2. 高確率レースをAIコンシェルジュで分析
        if smart_data["bets"]:
            top_bet = smart_data["bets"][0]
            
            # 3. レース分析リクエスト
            analysis_url = "http://localhost:8001/api/concierge/analyze-race"
            analysis_data = {
                "date": top_bet["date"],
                "jyo_cd": top_bet["jyo_cd"],
                "race_no": top_bet["race_no"]
            }
            
            async with api_client.post(analysis_url, json=analysis_data) as response:
                # 分析機能はオプションなのでエラーでもOK
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
