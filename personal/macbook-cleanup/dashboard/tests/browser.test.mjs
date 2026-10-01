import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp, mkdir, writeFile, readFile, rm, access, realpath} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {spawn} from 'node:child_process';

const skill = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const runtime = process.env.MACBOOK_PLAYWRIGHT_PATH;
const available = runtime && await access(path.join(skill, 'dashboard/dist/index.html')).then(() => true, () => false);

async function launch(chromium) {
  const executablePath = process.env.MACBOOK_BROWSER_PATH || chromium.executablePath();
  const present = await access(executablePath).then(() => true, () => false);
  return chromium.launch(present ? {headless: true, executablePath} : {headless: true, channel: 'chrome'});
}

async function waitFor(predicate, description, timeout = 15_000) {
  const end = Date.now() + timeout;
  while (Date.now() < end) {
    if (await predicate()) return;
    await new Promise(resolve => setTimeout(resolve, 50));
  }
  throw new Error(`Timed out: ${description}`);
}

async function fixture() {
  const home = await realpath(await mkdtemp(path.join(tmpdir(), 'macbook-dashboard-')));
  const report = path.join(home, 'report'), target = path.join(home, 'project/target');
  const archive = path.join(home, 'Downloads/install.zip'), models = path.join(home, '.ollama/models');
  for (const dir of [report, target, path.dirname(archive), models]) await mkdir(dir, {recursive: true});
  await writeFile(path.join(home, 'project/Cargo.toml'), '[package]\nname="dashboard-fixture"\n');
  await writeFile(path.join(target, 'artifact'), 'Disposable fixture data');
  await writeFile(archive, 'Replaceable fixture archive');
  const GiB = 1024 ** 3;
  const summary = {
    capacity: {total_bytes: 100 * GiB, used_bytes: 85 * GiB, free_bytes: 15 * GiB,
      used_percent: 85, target_percent: 50, reclaim_needed_bytes: 35 * GiB,
      measured_at: '2026-10-01T16:00:00Z', source: 'synthetic fixture'},
    coverage: {scope: 'synthetic fixture', elapsed_seconds: 0.1, files: 3, error_count: 0,
      dataless_skipped: 0, roots: [home], excluded: [], errors: []},
    limitations: ['Fixture only. No real user files.'], assessment: 'Review replaceable generated data.',
    candidates: [
      {path: target, category: 'build', allocated_bytes: 8 * GiB, logical_bytes: 8 * GiB},
      {path: archive, category: 'installer', allocated_bytes: GiB, logical_bytes: GiB},
      {path: models, category: 'models', allocated_bytes: 10 * GiB, logical_bytes: 10 * GiB},
    ],
  };
  await writeFile(path.join(report, 'summary.json'), JSON.stringify(summary));
  await writeFile(path.join(report, 'scan.json'), JSON.stringify({storage_categories: [
    {category: 'Projects', allocated_bytes: 30 * GiB},
    {category: 'Models', allocated_bytes: 10 * GiB},
    {category: 'Downloads', allocated_bytes: GiB},
  ]}));
  const code = `import sys,json\nsys.path.insert(0,sys.argv[1])\nfrom review_server import ReviewServer\ns=ReviewServer(sys.argv[2],preview=True,home=sys.argv[3],assets=sys.argv[4])\nprint(json.dumps({'url':s.url}),flush=True)\ns.serve_forever()\n`;
  const server = spawn(process.env.PYTHON || 'python3', ['-u', '-c', code, path.join(skill, 'scripts'),
    report, home, path.join(skill, 'dashboard/dist')], {stdio: ['ignore', 'pipe', 'pipe']});
  let output = '', stderr = '';
  server.stdout.on('data', data => {output += data.toString()});
  server.stderr.on('data', data => {stderr += data.toString()});
  await waitFor(() => output.includes('\n') || server.exitCode !== null, 'preview server readiness');
  assert.equal(server.exitCode, null, stderr);
  return {home, report, target, archive, server, url: JSON.parse(output.split('\n')[0]).url,
    output: () => output, stderr: () => stderr};
}

async function noOverflow(page, width, failures) {
  await page.setViewportSize({width, height: 950});
  await page.waitForTimeout(100);
  const dimensions = await page.evaluate(() => ({viewport: innerWidth,
    body: document.body.scrollWidth, document: document.documentElement.scrollWidth}));
  const pass = dimensions.body <= dimensions.viewport && dimensions.document <= dimensions.viewport;
  const message = `Horizontal overflow at ${width}px: ${JSON.stringify(dimensions)}`;
  if (failures) {if (!pass) failures.push(message)} else assert.ok(pass, message);
}

test('dashboard selection, exact review and final preview preserve fixture data', {skip: !available, timeout: 60_000}, async () => {
  const {chromium} = await import(pathToFileURL(runtime).href);
  const browser = await launch(chromium);
  const f = await fixture();
  const page = await browser.newPage({viewport: {width: 1440, height: 1100}});
  const errors = [], remote = [], overflow = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => {if (!request.url().startsWith(new URL(f.url).origin)) remote.push(request.url())});
  try {
    await page.goto(f.url);
    await page.getByRole('heading', {name: 'Make space for what’s next.'}).waitFor();
    assert.equal(await page.locator('.recharts-wrapper').count(), 2);
    await noOverflow(page, 1440, overflow);
    await noOverflow(page, 375, overflow);
    await noOverflow(page, 320, overflow);
    await page.setViewportSize({width: 1440, height: 1100});
    await page.getByRole('combobox', {name: 'Filter cleanup items'}).selectOption('models');
    assert.equal(await page.getByRole('checkbox').count(), 1);
    assert.equal(await page.getByRole('checkbox').isDisabled(), true);
    await page.getByRole('combobox', {name: 'Filter cleanup items'}).selectOption('selectable');
    assert.equal(await page.getByRole('checkbox').count(), 2);
    await page.getByRole('textbox', {name: 'Search cleanup items'}).fill('project');
    assert.equal(await page.getByRole('checkbox').count(), 1);
    const checkbox = page.getByRole('checkbox', {name: 'Select project · target'});
    await checkbox.focus();
    await page.keyboard.press('Space');
    assert.equal(await checkbox.getAttribute('aria-checked'), 'true');
    await page.getByRole('button', {name: 'Review 1 selected'}).click();
    const dialog = page.getByRole('alertdialog');
    await dialog.waitFor();
    assert.ok((await dialog.innerText()).includes(f.target));
    assert.ok((await dialog.innerText()).includes('never deletes files'));
    await noOverflow(page, 375, overflow);
    await page.setViewportSize({width: 1440, height: 1100});
    await dialog.getByRole('button', {name: 'Keep editing'}).click();
    assert.equal(await checkbox.getAttribute('aria-checked'), 'true');
    await page.getByRole('button', {name: 'Review 1 selected'}).click();
    await dialog.getByRole('button', {name: 'Confirm preview'}).click();
    await page.getByRole('status').filter({hasText: 'Preview saved. Nothing deleted.'}).waitFor();
    await access(path.join(f.target, 'artifact'));
    await access(f.archive);
    const result = JSON.parse(await readFile(path.join(f.report, 'cleanup-results.json'), 'utf8'));
    assert.equal(result.state, 'preview');
    assert.deepEqual(result.results.map(row => row.path), [f.target]);
    assert.equal(result.results[0].status, 'preview_only');
    assert.ok(f.output().includes('cleanup-result'), 'terminal receives final result');
    assert.equal(await page.getByRole('checkbox').isDisabled(), true);
    assert.deepEqual(errors, []);
    assert.deepEqual(remote, []);
    assert.equal(f.stderr(), '');
    assert.deepEqual(overflow, []);
  } finally {
    await browser.close();
    f.server.kill('SIGTERM');
    await rm(f.home, {recursive: true, force: true});
  }
});

test('saved dashboard charts work offline and cannot execute cleanup', {
  skip: !available || !process.env.MACBOOK_SAVED_REPORT, timeout: 30_000,
}, async () => {
  const {chromium} = await import(pathToFileURL(runtime).href);
  const browser = await launch(chromium);
  const page = await browser.newPage({viewport: {width: 1440, height: 1100}});
  const errors = [], requests = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => requests.push(request.url()));
  try {
    await page.goto(pathToFileURL(process.env.MACBOOK_SAVED_REPORT).href);
    await page.getByRole('heading', {name: 'Make space for what’s next.'}).waitFor();
    assert.ok((await page.locator('body').innerText()).includes('Saved report'));
    assert.equal(await page.locator('.recharts-wrapper').count(), 2);
    const selectable = page.getByRole('checkbox').filter({visible: true});
    for (let i = 0; i < await selectable.count(); i++) {
      if (!await selectable.nth(i).isDisabled()) {await selectable.nth(i).click(); break}
    }
    assert.equal(await page.getByRole('button', {name: /Review .*selected/}).isDisabled(), true);
    await noOverflow(page, 1440);
    await noOverflow(page, 375);
    assert.deepEqual(errors, []);
    assert.equal(requests.filter(url => /^https?:/.test(url)).length, 0);
  } finally {await browser.close()}
});

test('live dashboard screenshot is strictly read-only', {
  skip: !available || !process.env.MACBOOK_LIVE_REPORT || !process.env.MACBOOK_SCREENSHOT,
  timeout: 30_000,
}, async () => {
  const {chromium} = await import(pathToFileURL(runtime).href);
  const session = JSON.parse(await readFile(path.join(process.env.MACBOOK_LIVE_REPORT, 'review-session.json'), 'utf8'));
  const browser = await launch(chromium);
  const page = await browser.newPage({viewport: {width: 1440, height: 1180}, deviceScaleFactor: 1});
  const errors = [], mutations = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.route('**/api/**', route => {
    if (route.request().method() !== 'GET') {mutations.push(route.request().url()); return route.abort()}
    return route.continue();
  });
  try {
    await page.goto(session.url);
    await page.getByRole('heading', {name: 'Make space for what’s next.'}).waitFor();
    await page.screenshot({path: process.env.MACBOOK_SCREENSHOT, fullPage: true});
    assert.deepEqual(errors, []);
    assert.deepEqual(mutations, []);
  } finally {await browser.close()}
});
