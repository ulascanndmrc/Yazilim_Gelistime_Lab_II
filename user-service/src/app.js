require('dotenv').config();
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const userRoutes = require('./routes/userRoutes');

const app = express();
const PORT = process.env.PORT || 5003;
const MONGO_URI = process.env.MONGO_URI || 'mongodb://localhost:27017/user_db';

app.use(cors());
app.use(express.json());

// Health check (no auth needed)
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'user-service' });
});

// User routes
app.use('/api/users', userRoutes);

// Connect and start
mongoose.connect(MONGO_URI)
  .then(() => {
    console.log('[User Service] Connected to MongoDB');
    app.listen(PORT, () => console.log(`[User Service] Running on :${PORT}`));
  })
  .catch(err => {
    console.error('[User Service] MongoDB connection failed:', err);
    process.exit(1);
  });

module.exports = app;
