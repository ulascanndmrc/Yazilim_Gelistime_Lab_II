const mongoose = require('mongoose');

const userSchema = new mongoose.Schema({
  username:   { type: String, required: true, unique: true, trim: true },
  email:      { type: String, required: true, unique: true, lowercase: true },
  fullName:   { type: String, default: '' },
  bio:        { type: String, default: '' },
  avatarUrl:  { type: String, default: '' },
  isActive:   { type: Boolean, default: true },
}, { timestamps: true });

module.exports = mongoose.model('User', userSchema);
