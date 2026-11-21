// gta6-meme-x-01 round 2 entry (Node 22, standard library only).
//
// The entry is an X post, not a program: the meme (meme.jpg) is posted on X
// from a public account with make.fun (a link or written out) and/or a tag of
// @makefunai and the entrant's play code in its text, and POST.json names the
// post. This program's only job is to hand POST.json to the gate: it reads
// the file from the repository, checks it is a well-formed post address, and
// copies it byte for byte to /output/POST.json, then re-reads the copy to
// prove the write landed. Nothing this program writes is judged — the house
// reads the post itself from X.
//
//   mkdir -p out && MAKEFUN_BOT_DIR=. MAKEFUN_OUTPUT_DIR=out node main.ts
//   node main.ts --check        (validate POST.json without writing anything)

import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const BOT_DIR = process.env.MAKEFUN_BOT_DIR ?? "/bot";
const OUTPUT_DIR = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";
const MAX_POST_BYTES = 16384; // the gate's cap on POST.json

// An X post's address as the gate reads it: x.com or twitter.com (www. or
// mobile. allowed), /<handle>/status/<digits> or /i/web/status/<digits>;
// a query or fragment after it is read past.
const POST_URL_RE =
  /^https:\/\/(?:www\.|mobile\.)?(?:x\.com|twitter\.com)\/(?:[^/?#]+\/status\/\d+|i\/web\/status\/\d+)(?:[?#].*)?$/;

function fail(message: string): never {
  console.error(`gta6-meme-x-01: ${message}`);
  process.exit(1);
}

function readAndValidatePost(): { raw: Buffer; url: string } {
  const path = join(BOT_DIR, "POST.json");
  let raw: Buffer;
  try {
    raw = readFileSync(path);
  } catch (err) {
    fail(`could not read ${path}: ${(err as Error).message}`);
  }
  if (raw!.length === 0 || raw!.length > MAX_POST_BYTES) {
    fail(`POST.json is ${raw!.length} bytes (must be 1–${MAX_POST_BYTES})`);
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw!.toString("utf8"));
  } catch (err) {
    fail(`POST.json is not valid JSON: ${(err as Error).message}`);
  }
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    fail("POST.json must be a JSON object with a url field");
  }
  const url = (parsed as Record<string, unknown>).url;
  if (typeof url !== "string") {
    fail("POST.json url must be a string");
  }
  if (url.includes("<handle>") || url.includes("<id>")) {
    fail(
      "POST.json still holds the placeholder address — post the meme on X " +
        "and replace it with the post's real address first",
    );
  }
  if (!POST_URL_RE.test(url)) {
    fail(`POST.json url is not an X post address: ${url}`);
  }
  return { raw: raw!, url };
}

const checkOnly = process.argv.includes("--check");
const { raw, url } = readAndValidatePost();
if (checkOnly) {
  console.log(`POST.json OK: ${url} (${raw.length} bytes)`);
  process.exit(0);
}
mkdirSync(OUTPUT_DIR, { recursive: true });
const outPath = join(OUTPUT_DIR, "POST.json");
writeFileSync(outPath, raw);
// Re-read the copy: a short or torn write must fail loudly, not silently.
const written = readFileSync(outPath);
if (!written.equals(raw)) {
  fail(`${outPath} does not match POST.json after writing`);
}
console.log(`copied POST.json -> ${outPath} (${raw.length} bytes): ${url}`);
