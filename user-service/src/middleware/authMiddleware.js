const mongoose = require('mongoose');

const INTERNAL_API_KEY = process.env.INTERNAL_API_KEY || 'internal-dev-key';

/**
 * Middleware: reject requests that don't carry the dispatcher's internal API key.
 * Implements the second layer of authorization within the microservice.
 */
function verifyInternalKey(req, res, next) {
  const key = req.headers['x-internal-api-key'];
  if (key !== INTERNAL_API_KEY) {
    return res.status(403).json({ detail: 'Forbidden: direct access not allowed' });
  }
  next();
}

module.exports = { verifyInternalKey };
