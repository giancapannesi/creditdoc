import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const sourceRoot = path.join(root, 'src');
const distRoot = path.join(root, 'dist');
const sourceExtensions = new Set(['.astro', '.tsx', '.jsx', '.html', '.md', '.mdx']);

function walk(dir, predicate, files = []) {
  if (!fs.existsSync(dir)) return files;

  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walk(fullPath, predicate, files);
    } else if (predicate(fullPath)) {
      files.push(fullPath);
    }
  }

  return files;
}

function lineNumber(text, index) {
  return text.slice(0, index).split('\n').length;
}

function findImageAltIssues(filePath) {
  const text = fs.readFileSync(filePath, 'utf8');
  const issues = [];
  const imageTagPattern = /<img\b[^>]*>/gi;

  for (const match of text.matchAll(imageTagPattern)) {
    const tag = match[0];
    if (!/\salt\s*=/i.test(tag)) {
      issues.push({
        filePath,
        line: lineNumber(text, match.index),
        tag: tag.replace(/\s+/g, ' ').slice(0, 220),
      });
    }
  }

  return issues;
}

const sourceFiles = walk(sourceRoot, (filePath) => sourceExtensions.has(path.extname(filePath)));
const distFiles = walk(distRoot, (filePath) => path.extname(filePath) === '.html');
const issues = [...sourceFiles, ...distFiles].flatMap(findImageAltIssues);

if (issues.length > 0) {
  console.error(`[image-alt-contract] FAIL - ${issues.length} image(s) missing alt attributes.`);
  for (const issue of issues.slice(0, 100)) {
    console.error(`${path.relative(root, issue.filePath)}:${issue.line}: ${issue.tag}`);
  }
  if (issues.length > 100) {
    console.error(`[image-alt-contract] ...and ${issues.length - 100} more.`);
  }
  process.exit(1);
}

const sourceCount = sourceFiles.reduce((count, filePath) => {
  const text = fs.readFileSync(filePath, 'utf8');
  return count + (text.match(/<img\b/gi)?.length ?? 0);
}, 0);
const distCount = distFiles.reduce((count, filePath) => {
  const text = fs.readFileSync(filePath, 'utf8');
  return count + (text.match(/<img\b/gi)?.length ?? 0);
}, 0);

console.log(
  `[image-alt-contract] OK - ${sourceCount} source image tag(s) and ${distCount} rendered image tag(s) include alt attributes.`
);
