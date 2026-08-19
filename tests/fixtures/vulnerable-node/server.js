const express = require('express');
const _ = require('lodash');

const app = express();
app.use(express.json());
app.get('/health', (req, res) => res.json({ ok: true }));
app.post('/merge', (req, res) => res.json(_.merge({}, req.body)));
app.listen(process.env.PORT || 3000);
