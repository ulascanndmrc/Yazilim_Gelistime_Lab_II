/**
 * Jest tests for Product Service — TDD approach
 */
describe('Product Service — Internal Key Middleware', () => {
  const { verifyInternalKey } = require('../src/middleware/authMiddleware');

  test('allows request with correct internal key', () => {
    process.env.INTERNAL_API_KEY = 'internal-dev-key';
    const req = { headers: { 'x-internal-api-key': 'internal-dev-key' } };
    const res = { status: jest.fn().mockReturnThis(), json: jest.fn() };
    const next = jest.fn();
    verifyInternalKey(req, res, next);
    expect(next).toHaveBeenCalled();
  });

  test('rejects request with wrong key — returns 403', () => {
    const req = { headers: { 'x-internal-api-key': 'bad-key' } };
    const res = { status: jest.fn().mockReturnThis(), json: jest.fn() };
    const next = jest.fn();
    verifyInternalKey(req, res, next);
    expect(res.status).toHaveBeenCalledWith(403);
    expect(next).not.toHaveBeenCalled();
  });

  test('rejects missing key — returns 403', () => {
    const req = { headers: {} };
    const res = { status: jest.fn().mockReturnThis(), json: jest.fn() };
    const next = jest.fn();
    verifyInternalKey(req, res, next);
    expect(res.status).toHaveBeenCalledWith(403);
  });
});
