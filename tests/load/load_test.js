import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 10 }, // Ramp up to 10 users
    { duration: '5m', target: 10 }, // Stay at 10 users
    { duration: '2m', target: 20 }, // Ramp up to 20 users
    { duration: '5m', target: 20 }, // Stay at 20 users
    { duration: '2m', target: 0 },  // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% of requests must complete below 2s
    http_req_failed: ['rate<0.1'],     // Error rate must be below 10%
    errors: ['rate<0.1'],              // Custom error rate must be below 10%
  },
};

// Base URL for the API
const BASE_URL = 'http://localhost:8000';

// Test data
const symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'];
const indicatorTypes = ['ema', 'rsi'];

export default function () {
  // Test health endpoint
  const healthResponse = http.get(`${BASE_URL}/api/v1/health`);
  check(healthResponse, {
    'health check status is 200': (r) => r.status === 200,
    'health check response time < 500ms': (r) => r.timings.duration < 500,
  });
  errorRate.add(healthResponse.status !== 200);

  // Test quotes endpoint
  const quotesResponse = http.get(`${BASE_URL}/api/v1/quotes`);
  check(quotesResponse, {
    'quotes status is 200 or 404': (r) => r.status === 200 || r.status === 404,
    'quotes response time < 1000ms': (r) => r.timings.duration < 1000,
  });
  errorRate.add(quotesResponse.status !== 200 && quotesResponse.status !== 404);

  // Test quotes with symbol filter
  const randomSymbol = symbols[Math.floor(Math.random() * symbols.length)];
  const quotesBySymbolResponse = http.get(`${BASE_URL}/api/v1/quotes?symbol=${randomSymbol}`);
  check(quotesBySymbolResponse, {
    'quotes by symbol status is 200 or 404': (r) => r.status === 200 || r.status === 404,
    'quotes by symbol response time < 1000ms': (r) => r.timings.duration < 1000,
  });
  errorRate.add(quotesBySymbolResponse.status !== 200 && quotesBySymbolResponse.status !== 404);

  // Test latest quotes endpoint
  const latestQuotesResponse = http.get(`${BASE_URL}/api/v1/quotes/latest`);
  check(latestQuotesResponse, {
    'latest quotes status is 200 or 404': (r) => r.status === 200 || r.status === 404,
    'latest quotes response time < 1000ms': (r) => r.timings.duration < 1000,
  });
  errorRate.add(latestQuotesResponse.status !== 200 && latestQuotesResponse.status !== 404);

  // Test indicators endpoint
  const indicatorsResponse = http.get(`${BASE_URL}/api/v1/indicators`);
  check(indicatorsResponse, {
    'indicators status is 200 or 404': (r) => r.status === 200 || r.status === 404,
    'indicators response time < 1000ms': (r) => r.timings.duration < 1000,
  });
  errorRate.add(indicatorsResponse.status !== 200 && indicatorsResponse.status !== 404);

  // Test indicators with filters
  const randomIndicatorType = indicatorTypes[Math.floor(Math.random() * indicatorTypes.length)];
  const indicatorsByTypeResponse = http.get(`${BASE_URL}/api/v1/indicators?indicator_type=${randomIndicatorType}`);
  check(indicatorsByTypeResponse, {
    'indicators by type status is 200 or 404': (r) => r.status === 200 || r.status === 404,
    'indicators by type response time < 1000ms': (r) => r.timings.duration < 1000,
  });
  errorRate.add(indicatorsByTypeResponse.status !== 200 && indicatorsByTypeResponse.status !== 404);

  // Test latest indicators endpoint
  const latestIndicatorsResponse = http.get(`${BASE_URL}/api/v1/indicators/latest`);
  check(latestIndicatorsResponse, {
    'latest indicators status is 200 or 404': (r) => r.status === 200 || r.status === 404,
    'latest indicators response time < 1000ms': (r) => r.timings.duration < 1000,
  });
  errorRate.add(latestIndicatorsResponse.status !== 200 && latestIndicatorsResponse.status !== 404);

  // Test available indicators endpoint
  const availableIndicatorsResponse = http.get(`${BASE_URL}/api/v1/indicators/available`);
  check(availableIndicatorsResponse, {
    'available indicators status is 200': (r) => r.status === 200,
    'available indicators response time < 500ms': (r) => r.timings.duration < 500,
  });
  errorRate.add(availableIndicatorsResponse.status !== 200);

  // Test root endpoint
  const rootResponse = http.get(`${BASE_URL}/`);
  check(rootResponse, {
    'root status is 200': (r) => r.status === 200,
    'root response time < 500ms': (r) => r.timings.duration < 500,
  });
  errorRate.add(rootResponse.status !== 200);

  // Random sleep between requests (1-3 seconds)
  sleep(Math.random() * 2 + 1);
}

export function handleSummary(data) {
  return {
    'load_test_results.json': JSON.stringify(data, null, 2),
    'load_test_summary.txt': `
Load Test Summary
================
Total Requests: ${data.metrics.http_reqs.values.count}
Failed Requests: ${data.metrics.http_req_failed.values.count}
Error Rate: ${(data.metrics.http_req_failed.values.rate * 100).toFixed(2)}%
Average Response Time: ${data.metrics.http_req_duration.values.avg.toFixed(2)}ms
95th Percentile: ${data.metrics.http_req_duration.values['p(95)'].toFixed(2)}ms
Max Response Time: ${data.metrics.http_req_duration.values.max.toFixed(2)}ms
    `,
  };
}
