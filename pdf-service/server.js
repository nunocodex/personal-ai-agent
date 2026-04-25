const express = require("express");
const fs = require("fs");

const app = express();
app.use(express.json());

app.get("/health", (req, res) => {
  res.json({ status: "ok" });
});

app.post("/extract", async (req, res) => {
  const { file_path } = req.body;

  if (!file_path) return res.status(400).json({ error: "file_path is required" });
  if (!fs.existsSync(file_path)) return res.status(404).json({ error: `File not found: ${file_path}` });

  try {
    // pdf-parse may export as default or as named export depending on version
    let pdfParse = require("pdf-parse");
    if (pdfParse.default) pdfParse = pdfParse.default;

    const buffer = fs.readFileSync(file_path);
    const data = await pdfParse(buffer);

    res.json({
      text: data.text,
      pages: data.numpages,
      info: data.info,
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => console.log(`PDF service running on http://localhost:${PORT}`));