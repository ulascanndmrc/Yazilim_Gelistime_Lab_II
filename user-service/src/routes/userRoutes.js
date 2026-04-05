const express = require('express');
const router = express.Router();
const User = require('../models/User');
const { verifyInternalKey } = require('../middleware/authMiddleware');

// All routes require internal key
router.use(verifyInternalKey);

// GET /api/users — list all users
router.get('/', async (req, res) => {
  try {
    const { limit = 50, page = 1 } = req.query;
    const users = await User.find({ isActive: true })
      .select('-__v')
      .limit(Number(limit))
      .skip((Number(page) - 1) * Number(limit))
      .sort({ createdAt: -1 });
    return res.status(200).json(users);
  } catch (err) {
    return res.status(500).json({ detail: 'Internal server error' });
  }
});

// POST /api/users — create user
router.post('/', async (req, res) => {
  try {
    const { username, email, fullName, bio, avatarUrl } = req.body;
    if (!username || !email) {
      return res.status(422).json({ detail: 'username and email are required' });
    }
    const user = await User.create({ username, email, fullName, bio, avatarUrl });
    return res.status(201).json(user);
  } catch (err) {
    if (err.code === 11000) {
      return res.status(409).json({ detail: 'Username or email already exists' });
    }
    return res.status(500).json({ detail: 'Internal server error' });
  }
});

// GET /api/users/:id — get by ID
router.get('/:id', async (req, res) => {
  try {
    const user = await User.findById(req.params.id).select('-__v');
    if (!user) return res.status(404).json({ detail: 'User not found' });
    return res.status(200).json(user);
  } catch (err) {
    return res.status(422).json({ detail: 'Invalid user ID' });
  }
});

// PUT /api/users/:id — update user
router.put('/:id', async (req, res) => {
  try {
    const allowed = ['fullName', 'bio', 'avatarUrl', 'isActive'];
    const updates = {};
    allowed.forEach(f => { if (req.body[f] !== undefined) updates[f] = req.body[f]; });

    const user = await User.findByIdAndUpdate(
      req.params.id, { $set: updates }, { new: true, runValidators: true }
    ).select('-__v');
    if (!user) return res.status(404).json({ detail: 'User not found' });
    return res.status(200).json(user);
  } catch (err) {
    return res.status(422).json({ detail: 'Invalid request' });
  }
});

// DELETE /api/users/:id — soft delete
router.delete('/:id', async (req, res) => {
  try {
    const user = await User.findByIdAndUpdate(
      req.params.id, { isActive: false }, { new: true }
    );
    if (!user) return res.status(404).json({ detail: 'User not found' });
    return res.status(204).send();
  } catch (err) {
    return res.status(422).json({ detail: 'Invalid user ID' });
  }
});

module.exports = router;
