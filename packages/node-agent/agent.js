const { marker } = require("@squarediff-smoke/node-shared");

const input = process.argv[2] || "";
const cwd = process.cwd().split("/").pop();
console.log(`node-package-agent|input=${input}|marker=${marker()}|cwd=${cwd}`);
