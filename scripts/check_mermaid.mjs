// Parse every book diagram with the pinned Mermaid parser.
import { readdir, readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { JSDOM } from 'jsdom';

const dom = new JSDOM('<!doctype html><html><body></body></html>');
globalThis.window = dom.window;
globalThis.document = dom.window.document;
const { default: mermaid } = await import('mermaid');
mermaid.initialize({ startOnLoad: false });
const root = fileURLToPath(new URL('../', import.meta.url));

async function* markdownFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  for (const entry of entries.sort((a, b) => a.name.localeCompare(b.name))) {
    if (entry.name.startsWith('.') || entry.name === 'node_modules') continue;
    const filename = path.join(directory, entry.name);
    if (entry.isDirectory()) yield* markdownFiles(filename);
    else if (entry.isFile() && entry.name.endsWith('.md')) yield filename;
  }
}

let count = 0;
let failures = 0;
for await (const filename of markdownFiles(root)) {
  const markdown = await readFile(filename, 'utf8');
  let fence;
  let diagram;
  let start;
  const lines = markdown.split(/\r?\n/);
  for (let index = 0; index < lines.length; index++) {
    const line = lines[index];
    const marker = line.match(/^\s*(`{3,}|~{3,})(.*)$/);
    if (!fence && marker) {
      fence = marker[1];
      start = index + 1;
      diagram = marker[2].trim() === 'mermaid' ? [] : undefined;
    } else if (fence && marker && marker[1][0] === fence[0]
      && marker[1].length >= fence.length && !marker[2].trim()) {
      if (diagram) {
        count++;
        try { await mermaid.parse(diagram.join('\n')); }
        catch (error) {
          failures++;
          console.error(`${path.relative(root, filename)}:${start}\n${error.message}`);
        }
      }
      fence = undefined;
      diagram = undefined;
    } else if (diagram) diagram.push(line);
  }
  if (fence) {
    failures++;
    console.error(`${path.relative(root, filename)}:${start}: unclosed code fence`);
  }
}
if (!count) {
  failures++;
  console.error('No Mermaid diagrams found');
}
console.log(`${count} Mermaid diagrams, ${failures} errors`);
dom.window.close();
process.exitCode = failures ? 1 : 0;
