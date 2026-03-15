import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Hatalı (4xx ve 5xx) ve Başarılı (2xx) istekleri oranlamak için metrikler
export const errorRate = new Rate('errors');
export const successRate = new Rate('success');

// Test Konfigürasyonu: Kademeli artan Yük Testi (50 -> 100 -> 200 -> 500)
export const options = {
  stages: [
    { duration: '30s', target: 50 },  // 30 saniyede 50 kullanıcıya çık
    { duration: '30s', target: 100 }, // 30 saniyede 100 kullanıcıya çık
    { duration: '1m', target: 200 },  // 1 dakikada 200 kullanıcıya çık
    { duration: '1m', target: 500 },  // 1 dakikada 500 kullanıcıya çık
    { duration: '30s', target: 0 },   // 30 saniyede sıfıra in (shutdown)
  ],
  thresholds: {
    errors: ['rate<0.05'], // Hata oranı %5'ten az olmalı
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

// Setup aşaması: Tüm Sanal Kullanıcılar (VUs) için öncelikle bir kere çalışır.
// Testin kullanacağı geçerli bir token almak için kullanıcı kaydı ve girişi yapar.
export function setup() {
  const username = `k6_test_user_${Date.now()}`;
  const password = `TestPass123!`;

  const headers = { 'Content-Type': 'application/json' };

  // 1. Kullanıcı Kaydı (Register)
  http.post(`${BASE_URL}/auth/register`, JSON.stringify({
    username: username,
    email: `${username}@test.com`,
    password: password
  }), { headers });

  // 2. Kullanıcı Girişi (Login) - Token Alımı
  const loginRes = http.post(`${BASE_URL}/auth/login`, JSON.stringify({
    username: username,
    password: password
  }), { headers });

  let token = '';
  if (loginRes.status === 200) {
    const body = loginRes.json();
    token = body.access_token;
  }

  return { token: token }; // Her VU'ya bu veriyi dağıt (data nesnesi olarak)
}

// Her Sanal Kullanıcının (VU) sürekli çalıştırdığı ana fonksiyon
export default function (data) {
  // Eğer setup'tan alınan geçerli bir token varsa, Bearer Authorization ekle
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${data.token}`
  };

  // Senaryo seçimi (%30 Login, %40 Get Products, %30 Post Messages)
  const rand = Math.random();

  let res;

  if (rand < 0.3) {
    // Senaryo 1: Rastgele geçersiz veya geçerli kullanıcı ile oturum açma (POST /auth/login)
    const payload = JSON.stringify({
      username: `k6_random_${Math.floor(Math.random() * 1000)}`,
      password: 'RandomPassword123'
    });
    res = http.post(`${BASE_URL}/auth/login`, payload, { headers: { 'Content-Type': 'application/json' } });
  } 
  else if (rand < 0.7) {
    // Senaryo 2: Ürünleri listeleme (GET /api/products)
    res = http.get(`${BASE_URL}/api/products`, { headers });
  } 
  else {
    // Senaryo 3: Yeni mesaj gönderme (POST /api/messages)
    const payload = JSON.stringify({
      content: `K6 Load Test Mesajı ${__VU}-${__ITER}`,
      channel: "load-test"
    });
    res = http.post(`${BASE_URL}/api/messages`, payload, { headers });
  }

  // Durum kodlarına göre Başarı ve Hata oranlarını say (2xx Başarılı, gerisi Hatalı)
  const isSuccess = res.status >= 200 && res.status < 300;
  
  if (isSuccess) {
    successRate.add(1);
  } else {
    errorRate.add(1);
  }

  // k6 check(doğrulama) ile arayüzde başarılı olanları gösteriyoruz
  check(res, {
    'Başarılı İstek (HTTP 2xx)': (r) => r.status >= 200 && r.status < 300,
    'Hatalı İstek (HTTP 4xx/5xx)': (r) => r.status >= 400,
  });

  // Kullanıcının ardışık istekleri arasında yoğunluğu simüle eden küçük bekleme süresi
  sleep(Math.random() * 1.5 + 0.5); // 0.5 ile 2.0 saniye arası bekle
}

export function teardown(data) {
  console.log("==================================================");
  console.log(" K6 Yük Testi (Load Test) Başarıyla Tamamlandı!   ");
  console.log("==================================================");
}