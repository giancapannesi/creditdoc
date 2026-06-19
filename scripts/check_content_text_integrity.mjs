import { readdirSync, readFileSync } from 'node:fs';
import { join, relative } from 'node:path';

const rootDir = 'src/content';
const controlCharacterPattern = /[\u0000-\u0008\u000B\u000C\u000E-\u001F]/;
const mangledCurrencyRangePattern = /(^|\s)\\,[0-9]{3}\s*-/;
const findings = [];

function jsonFiles(dir) {
  const entries = readdirSync(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...jsonFiles(path));
    } else if (entry.isFile() && entry.name.endsWith('.json')) {
      files.push(path);
    }
  }
  return files;
}

function visit(value, path, file) {
  if (typeof value === 'string') {
    const isLegacyAddressField = path === '$.address';
    if (!isLegacyAddressField && controlCharacterPattern.test(value)) {
      findings.push({ file, path, type: 'control_character' });
    }
    if (mangledCurrencyRangePattern.test(value)) {
      findings.push({ file, path, type: 'mangled_currency_range', value });
    }
    return;
  }
  if (Array.isArray(value)) {
    value.forEach((item, index) => visit(item, `${path}[${index}]`, file));
    return;
  }
  if (value && typeof value === 'object') {
    for (const [key, item] of Object.entries(value)) {
      visit(item, path ? `${path}.${key}` : key, file);
    }
  }
}

for (const filePath of jsonFiles(rootDir)) {
  const file = relative(process.cwd(), filePath);
  let data;
  try {
    data = JSON.parse(readFileSync(filePath, 'utf8'));
  } catch (error) {
    findings.push({ file, path: '$', type: 'invalid_json', error: error.message });
    continue;
  }
  visit(data, '$', file);
}

if (findings.length > 0) {
  console.error(JSON.stringify({ ok: false, findings }, null, 2));
  process.exit(1);
}

console.log(JSON.stringify({ ok: true, checkedDir: rootDir }));
