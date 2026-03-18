const express = require('express');
const path = require('path');
const app = express();

const PORT = process.env.PORT || 3000;

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'exylio-v2.html'));
});

app.listen(PORT, () => {
  console.log(`Exylio running on port ${PORT}`);
});