// server.js
const express = require("express");
const { spawn } = require("child_process");

const app = express();
app.use(express.json());

app.post("/run-command", (req, res) => {
  const { command } = req.body;

  // SSE headers
  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");

  const cmd = spawn(command, { shell: true });

  cmd.stdout.on("data", (data) => {
    res.write(`data: ${data.toString()}\n\n`);
  });

  cmd.stderr.on("data", (data) => {
    res.write(`data: ${data.toString()}\n\n`);
  });

  cmd.on("close", (code) => {
    res.write(`data: Command exited with code ${code}\n\n`);
    res.end();
  });
});

app.listen(5000, () => console.log("Server running on port 5000"));
