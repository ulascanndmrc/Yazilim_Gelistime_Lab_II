/**
 * Jest tests for User Service — TDD approach
 * Tests the route handlers with mocked middleware
 */
const request = require('supertest');

// Mock mongoose before requiring app
jest.mock('mongoose', () => {
  const actual = jest.requireActual('mongoose');
  return {
    ...actual,
    connect: jest.fn().mockResolvedValue(true),
    model: jest.fn().mockReturnValue({}),
  };
});

describe('User Service — Internal Key Middleware', () => {
  const { verifyInternalKey } = require('../src/middleware/authMiddleware');

  test('allows request with correct internal key', () => {
    const req = { headers: { 'x-internal-api-key': 'internal-dev-key' } };
    const res = { status: jest.fn().mockReturnThis(), json: jest.fn() };
    const next = jest.fn();
    process.env.INTERNAL_API_KEY = 'internal-dev-key';
    verifyInternalKey(req, res, next);
    expect(next).toHaveBeenCalled();
  });

  test('rejects request with wrong key', () => {
    const req = { headers: { 'x-internal-api-key': 'wrong-key' } };
    const res = { status: jest.fn().mockReturnThis(), json: jest.fn() };
    const next = jest.fn();
    verifyInternalKey(req, res, next);
    expect(res.status).toHaveBeenCalledWith(403);
    expect(next).not.toHaveBeenCalled();
  });

  test('rejects request with no key', () => {
    const req = { headers: {} };
    const res = { status: jest.fn().mockReturnThis(), json: jest.fn() };
    const next = jest.fn();
    verifyInternalKey(req, res, next);
    expect(res.status).toHaveBeenCalledWith(403);
  });
});
