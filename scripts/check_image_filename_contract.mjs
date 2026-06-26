import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const publicRoot = path.join(root, 'public');
const imageExtensions = new Set(['.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg']);
const weakNamePattern = /^(image|img|photo|picture|screenshot|untitled|download|file|logo|\d+)$/i;

function walk(dir, files = []) {
  if (!fs.existsSync(dir)) return files;

  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walk(fullPath, files);
    } else if (imageExtensions.has(path.extname(entry.name).toLowerCase())) {
      files.push(fullPath);
    }
  }

  return files;
}

const issues = [];

for (const filePath of walk(publicRoot)) {
  const filename = path.basename(filePath);
  const ext = path.extname(filename);
  const stem = filename.slice(0, -ext.length);

  if (/\s/.test(filename)) {
    issues.push([filePath, 'contains whitespace']);
  }
  if (/[A-Z]/.test(filename)) {
    issues.push([filePath, 'contains uppercase letters']);
  }
  if (weakNamePattern.test(stem)) {
    issues.push([filePath, 'uses a generic or numeric-only filename']);
  }
}

if (issues.length > 0) {
  console.error(`[image-filename-contract] FAIL - ${issues.length} image filename issue(s).`);
  for (const [filePath, reason] of issues.slice(0, 100)) {
    console.error(`${path.relative(root, filePath)}: ${reason}`);
  }
  if (issues.length > 100) {
    console.error(`[image-filename-contract] ...and ${issues.length - 100} more.`);
  }
  process.exit(1);
}

console.log(`[image-filename-contract] OK - ${walk(publicRoot).length} public image filename(s) checked.`);
