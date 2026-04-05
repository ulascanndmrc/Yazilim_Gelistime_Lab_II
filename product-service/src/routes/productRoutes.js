const express = require('express');
const router = express.Router();
const Product = require('../models/Product');
const { verifyInternalKey } = require('../middleware/authMiddleware');

// All routes require internal key
router.use(verifyInternalKey);

// GET /api/products
router.get('/', async (req, res) => {
  try {
    const { category, limit = 50, page = 1 } = req.query;
    const query = { isAvailable: true };
    if (category) query.category = category;
    const products = await Product.find(query)
      .select('-__v')
      .limit(Number(limit))
      .skip((Number(page) - 1) * Number(limit))
      .sort({ createdAt: -1 });
    return res.status(200).json(products);
  } catch (err) {
    return res.status(500).json({ detail: 'Internal server error' });
  }
});

// POST /api/products
router.post('/', async (req, res) => {
  try {
    const userId = req.headers['x-user-id'];
    if (!userId) return res.status(401).json({ detail: 'User identity missing' });
    const { name, description, price, category, stock, imageUrl } = req.body;
    if (!name || price === undefined) {
      return res.status(422).json({ detail: 'name and price are required' });
    }
    const product = await Product.create({
      name, description, price, category, stock, imageUrl, sellerId: userId
    });
    return res.status(201).json(product);
  } catch (err) {
    return res.status(500).json({ detail: 'Internal server error' });
  }
});

// GET /api/products/:id
router.get('/:id', async (req, res) => {
  try {
    const product = await Product.findById(req.params.id).select('-__v');
    if (!product) return res.status(404).json({ detail: 'Product not found' });
    return res.status(200).json(product);
  } catch (err) {
    return res.status(422).json({ detail: 'Invalid product ID' });
  }
});

// PUT /api/products/:id
router.put('/:id', async (req, res) => {
  try {
    const userId = req.headers['x-user-id'];
    const allowed = ['name', 'description', 'price', 'category', 'stock', 'imageUrl', 'isAvailable'];
    const updates = {};
    allowed.forEach(f => { if (req.body[f] !== undefined) updates[f] = req.body[f]; });

    const product = await Product.findById(req.params.id);
    if (!product) return res.status(404).json({ detail: 'Product not found' });
    if (product.sellerId !== userId) {
      return res.status(403).json({ detail: 'Cannot modify another seller\'s product' });
    }
    Object.assign(product, updates);
    await product.save();
    return res.status(200).json(product);
  } catch (err) {
    return res.status(422).json({ detail: 'Invalid request' });
  }
});

// DELETE /api/products/:id
router.delete('/:id', async (req, res) => {
  try {
    const userId = req.headers['x-user-id'];
    const product = await Product.findById(req.params.id);
    if (!product) return res.status(404).json({ detail: 'Product not found' });
    if (product.sellerId !== userId) {
      return res.status(403).json({ detail: 'Cannot delete another seller\'s product' });
    }
    product.isAvailable = false;
    await product.save();
    return res.status(204).send();
  } catch (err) {
    return res.status(422).json({ detail: 'Invalid product ID' });
  }
});

module.exports = router;
