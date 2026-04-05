#!/bin/bash
# Tüm servisleri test eden script
BASE="http://localhost:8000"

echo "======================================"
echo "  DISPATCHER SMOKE TEST"
echo "======================================"
echo ""

# 1. Health check
echo "[1] Health Check..."
curl -s $BASE/health
echo -e "\n"

# 2. Servis sağlığı
echo "[2] Tüm Servislerin Sağlık Durumu..."
curl -s $BASE/api/gateway/health | python3 -m json.tool
echo ""

# 3. Kayıt ol
echo "[3] Kullanıcı Kayıt (Register)..."
REGISTER=$(curl -s -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@test.com","password":"Test123!"}')
echo $REGISTER | python3 -m json.tool 2>/dev/null || echo $REGISTER
echo ""

# 4. Login
echo "[4] Login (Token Al)..."
LOGIN=$(curl -s -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"Test123!"}')
echo $LOGIN | python3 -m json.tool 2>/dev/null || echo $LOGIN

TOKEN=$(echo $LOGIN | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token',''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  echo "Token alinamadi, cikiliyor."
  exit 1
fi
echo "Token: ${TOKEN:0:40}..."
echo ""

# 5. Token olmadan istek (401 bekleniyor)
echo "[5] Token Olmadan İstek (401 bekleniyor)..."
curl -s -o /dev/null -w "HTTP Status: %{http_code}" $BASE/api/messages
echo -e "\n"

# 6. Token ile mesaj oluştur
echo "[6] Mesaj Oluştur (Message Service)..."
curl -s -X POST $BASE/api/messages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"Merhaba Mikroservis!","channel":"genel"}' | python3 -m json.tool
echo ""

# 7. Mesaj listesi
echo "[7] Mesajları Listele..."
curl -s $BASE/api/messages \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

# 8. Ürün oluştur
echo "[8] Ürün Oluştur (Product Service)..."
curl -s -X POST $BASE/api/products \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Ürünü","price":99.99,"category":"elektronik","stock":50}' | python3 -m json.tool
echo ""

# 9. Rapor oluştur
echo "[9] Rapor Oluştur (Report Service)..."
curl -s -X POST $BASE/api/reports \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"report_type":"traffic","title":"İlk Test Raporu","description":"Smoke test"}' | python3 -m json.tool
echo ""

# 10. Gateway istatistikleri
echo "[10] Gateway İstatistikleri..."
curl -s $BASE/api/gateway/stats | python3 -m json.tool
echo ""

# 11. Bilinmeyen rota (404 bekleniyor)
echo "[11] Bilinmeyen Rota (404 bekleniyor)..."
curl -s -o /dev/null -w "HTTP Status: %{http_code}" $BASE/api/bilinmeyen
echo -e "\n"

echo "======================================"
echo "  TEST TAMAMLANDI"
echo "  Dashboard: http://localhost:8000/dashboard"
echo "  Grafana:   http://localhost:3000  (admin/admin123)"
echo "======================================"
