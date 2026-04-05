const mongoose = require('mongoose');

const productSchema = new mongoose.Schema({
  name:        { type: String, required: true, trim: true },
  description: { type: String, default: '' },
  price:       { type: Number, required: true, min: 0 },
  category:    { type: String, default: 'general' },
  stock:       { type: Number, default: 0, min: 0 },
  sellerId:    { type: String, required: true },
  isAvailable: { type: Boolean, default: true },
  imageUrl:    { type: String, default: '' },
}, { timestamps: true });

productSchema.index({ category: 1 });
productSchema.index({ sellerId: 1 });

module.exports = mongoose.model('Product', productSchema);
