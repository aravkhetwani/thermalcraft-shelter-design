import express from 'express';
import cors from 'cors';
import apiRouter from './routes/api.js';

const app = express();
const PORT = process.env.PORT || 4000;

app.use(cors());
app.use(express.json());
app.use('/api', apiRouter);

app.get('/', (req, res) => {
  res.send('High Altitude Shelter Model — mock API server. See /api/materials, /api/climate, /api/simulation-result');
});

app.listen(PORT, () => {
  console.log(`Mock API server running at http://localhost:${PORT}`);
});
