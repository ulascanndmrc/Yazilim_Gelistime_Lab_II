require('dotenv').config();
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const productRoutes = require('./routes/productRoutes');

const app = express();
const PORT = process.env.PORT || 5004;
const MONGO_URI = process.env.MONGO_URI || 'mongodb://localhost:27017/product_db';

app.use(cors());
app.use(express.json());

app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'product-service' });
});

app.use('/api/products', productRoutes);

mongoose.connect(MONGO_URI)
  .then(() => {
    console.log('[Product Service] Connected to MongoDB');
    app.listen(PORT, () => console.log(`[Product Service] Running on :${PORT}`));
  })
  .catch(err => {
    console.error('[Product Service] MongoDB connection failed:', err);
    process.exit(1);
  });

module.exports = app;
