require('dotenv').config();
const express = require('express');
const { execFile } = require('child_process');
const path = require('path');
const cors = require('cors');

const app = express();
const port = process.env.PORT || 4000;

// Optional: whitelist only your frontend origins for CORS
const allowedOrigins = [
  'https://animerecoms.onrender.com',
  'http://localhost:3000',
];

app.use(cors({
  origin: function(origin, callback) {
    if (!origin) return callback(null, true); // allow requests with no origin (like curl, mobile)
    if (allowedOrigins.indexOf(origin) === -1) {
      return callback(new Error(`CORS policy does not allow access from origin ${origin}`), false);
    }
    callback(null, true);
  },
  credentials: true
}));

app.get('/recommend', (req, res) => {
  const animeName = req.query.anime;

  if (!animeName) {
    return res.status(400).json({ Error: "Anime name is required" });
  }

  const pythonScriptPath = path.join(__dirname, '..', 'python', 'anime_recom.py');

  execFile('python', [pythonScriptPath, animeName], (error, stdout, stderr) => {
    if (error) {
      return res.status(500).json({ Error: 'Error executing the Python script', Details: error.message });
    }
    if (stderr) {
      return res.status(500).json({ Error: 'Python script error', Details: stderr });
    }

    try {
      const result = JSON.parse(stdout);
      res.json(result);
    } catch (parseError) {
      res.status(500).json({ Error: "Error parsing Python script output", Details: parseError.message });
    }
  });
});

app.listen(port, '0.0.0.0', () => {
  console.log(`Server listening on port ${port}`);
});
