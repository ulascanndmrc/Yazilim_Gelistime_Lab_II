/**
 * k6 Load Testing Script — Dispatcher API Gateway
 * Tests: 50, 100, 200, 500 Virtual Users
 *
 * Run: k6 run k6_script.js
 * Run with VUs: k6 run --vus 100 --duration 30s k6_script.js
 */
import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// ─── Custom Metrics ──────────────────────────────────────────────────────────
const errorRate       = new Rate('error_rate');
const routingAccuracy = new Rate('routing_accuracy');
const loginLatency    = new Trend('login_latency_ms');
const messageLatency  = new Trend('message_latency_ms');
const userLatency     = new Trend('user_latency_ms');
const productLatency  = new Trend('product_latency_ms');
const reportLatency   = new Trend('report_latency_ms');
const totalRequests   = new Counter('total_requests');

// ─── Configuration ────────────────────────────────────────────────────────────
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export const options = {
  scenarios: {
    load_50: {
      executor: 'constant-vus',
      vus: 50,
      duration: '30s',
      startTime: '0s',
      tags: { scenario: 'vus_50' },
    },
    load_100: {
      executor: 'constant-vus',
      vus: 100,
      duration: '30s',
      startTime: '35s',
      tags: { scenario: 'vus_100' },
    },
    load_200: {
      executor: 'constant-vus',
      vus: 200,
      duration: '30s',
      startTime: '70s',
      tags: { scenario: 'vus_200' },
    },
    load_500: {
      executor: 'constant-vus',
      vus: 500,
      duration: '30s',
      startTime: '105s',
      tags: { scenario: 'vus_500' },
    },
  },
  thresholds: {
    http_req_duration:  ['p(95)<2000'],
    error_rate:         ['rate<0.05'],
    routing_accuracy:   ['rate>0.95'],
  },
};

// ─── Shared state ─────────────────────────────────────────────────────────────
let authToken = '';

// ─── Setup: create test user and get token ────────────────────────────────────
export function setup() {
  const username = `loadtest_${Date.now()}`;

  // Register
  const regRes = http.post(`${BASE_URL}/auth/register`, JSON.stringify({
    username, email: `${username}@test.com`, password: 'TestPass123!', role: 'user'
  }), { headers: { 'Content-Type': 'application/json' } });

  // Login
  const loginRes = http.post(`${BASE_URL}/auth/login`, JSON.stringify({
    username, password: 'TestPass123!'
  }), { headers: { 'Content-Type': 'application/json' } });

  const body = JSON.parse(loginRes.body || '{}');
  return { token: body.access_token || '' };
}

// ─── Main test function ───────────────────────────────────────────────────────
export default function (data) {
  const token = data.token;
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  };

  group('Health Check', () => {
    const res = http.get(`${BASE_URL}/health`);
    totalRequests.add(1);
    const ok = check(res, { 'health 200': (r) => r.status === 200 });
    errorRate.add(!ok);
    routingAccuracy.add(ok);
  });

  group('Auth — Login', () => {
    const start = Date.now();
    const res = http.post(`${BASE_URL}/auth/login`, JSON.stringify({
      username: 'nonexistent_user_test', password: 'wrong'
    }), { headers: { 'Content-Type': 'application/json' } });
    loginLatency.add(Date.now() - start);
    totalRequests.add(1);
    const ok = check(res, { 'auth routed (401 expected)': (r) => r.status === 401 || r.status === 200 });
    routingAccuracy.add(ok);
    errorRate.add(res.status >= 500);
  });

  group('Messages Service', () => {
    const start = Date.now();
    const res = http.get(`${BASE_URL}/api/messages`, { headers });
    messageLatency.add(Date.now() - start);
    totalRequests.add(1);
    const ok = check(res, {
      'message service responds': (r) => r.status !== 503 && r.status !== 504,
      'message status valid': (r) => [200, 401, 403].includes(r.status),
    });
    errorRate.add(res.status >= 500);
    routingAccuracy.add(res.status !== 404);
  });

  group('User Service', () => {
    const start = Date.now();
    const res = http.get(`${BASE_URL}/api/users`, { headers });
    userLatency.add(Date.now() - start);
    totalRequests.add(1);
    const ok = check(res, {
      'user service responds': (r) => r.status !== 503 && r.status !== 504,
    });
    errorRate.add(res.status >= 500);
    routingAccuracy.add(res.status !== 404);
  });

  group('Product Service', () => {
    const start = Date.now();
    const res = http.get(`${BASE_URL}/api/products`, { headers });
    productLatency.add(Date.now() - start);
    totalRequests.add(1);
    const ok = check(res, {
      'product service responds': (r) => r.status !== 503 && r.status !== 504,
    });
    errorRate.add(res.status >= 500);
    routingAccuracy.add(res.status !== 404);
  });

  group('Report Service', () => {
    const start = Date.now();
    const res = http.get(`${BASE_URL}/api/reports`, { headers });
    reportLatency.add(Date.now() - start);
    totalRequests.add(1);
    const ok = check(res, {
      'report service responds': (r) => r.status !== 503 && r.status !== 504,
    });
    errorRate.add(res.status >= 500);
    routingAccuracy.add(res.status !== 404);
  });

  group('Invalid Route — 404 expected', () => {
    const res = http.get(`${BASE_URL}/api/nonexistent-service`, { headers });
    totalRequests.add(1);
    const correct404 = check(res, { 'returns 404 for unknown route': (r) => r.status === 404 });
    routingAccuracy.add(correct404);
    errorRate.add(!correct404 && res.status >= 500);
  });

  group('Unauthorized — no token', () => {
    const res = http.get(`${BASE_URL}/api/messages`);
    totalRequests.add(1);
    const correct401 = check(res, { 'returns 401 without token': (r) => r.status === 401 });
    routingAccuracy.add(correct401);
  });

  sleep(0.1);
}

// ─── Teardown: print summary ──────────────────────────────────────────────────
export function teardown(data) {
  console.log('Load test complete. Check results above.');
}
