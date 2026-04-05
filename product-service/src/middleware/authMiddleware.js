const mongoose = require('mongoose');

/**
 * Middleware: reject requests that don't carry the dispatcher's internal API key.
 */
function verifyInternalKey(req, res, next) {
  const key = req.headers['x-internal-api-key'];
  const expected = process.env.INTERNAL_API_KEY || 'internal-dev-key';
  if (key !== expected) {
    return res.status(403).json({ detail: 'Forbidden: direct access not allowed' });
  }
  next();
}

module.exports = { verifyInternalKey };
