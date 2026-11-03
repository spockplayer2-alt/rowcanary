'use strict';
const $ = id => document.getElementById(id);
let mode = 'make';
let current = null;
const themeButton = $('theme');
function theme(value) {
  document.documentElement.dataset.theme = value;
  themeButton.textContent = value === 'dark' ? 'Light theme' : 'Dark theme';
  themeButton.setAttribute('aria-label', 'Switch to ' + (value === 'dark' ? 'light' : 'dark') + ' theme');
}
let initial = matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
try { initial = localStorage.getItem('rowcanary-theme') || initial; } catch (_) {}
theme(initial === 'dark' ? 'dark' : 'light');
themeButton.addEventListener('click', () => {
  const value = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  theme(value);
  try { localStorage.setItem('rowcanary-theme', value); } catch (_) {}
});
function setMode(value) {
  if (mode !== value) clearReport();
  mode = value;
  $('step-make').classList.toggle('active', mode === 'make');
  $('step-check').classList.toggle('active', mode === 'check');
  $('step-make').setAttribute('aria-pressed', String(mode === 'make'));
  $('step-check').setAttribute('aria-pressed', String(mode === 'check'));
  $('upload-section').hidden = mode !== 'check';
  $('upload').required = mode === 'check';
  $('id-column').disabled = $('value-column').disabled = mode === 'make';
  $('panel-eyebrow').textContent = mode === 'make' ? 'Before your import' : 'After your export';
  $('panel-title').textContent = mode === 'make' ? 'Start with values you can trust.' : 'See what came back unchanged.';
  $('panel-description').textContent = mode === 'make' ? 'Generate a test file, pass it through an isolated import/export workflow, then bring the export back here.' : 'Choose the exported control file. Use the same control set and custom values you used when generating it.';
  $('submit').textContent = mode === 'make' ? 'Download controls ↓' : 'Check export →';
  $('status').textContent = '';
}
$('step-make').addEventListener('click', () => setMode('make'));
$('step-check').addEventListener('click', () => setMode('check'));
function clearReport() {
  current = null;
  $('results').hidden = true;
}
$('controls').addEventListener('input', clearReport);
$('upload').addEventListener('change', () => {
  const file = $('upload').files[0];
  const extension = file?.name.split('.').pop().toLowerCase();
  if (['csv', 'tsv', 'json', 'jsonl', 'xlsx'].includes(extension)) $('format').value = extension;
});
function download(content, filename, type) {
  const url = URL.createObjectURL(new Blob([content], {type}));
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 30000);
}
function fileData(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result.split(',')[1]);
    reader.onerror = () => reject(new Error('The file could not be read.'));
    reader.readAsDataURL(file);
  });
}
function showReport(report) {
  $('results').hidden = false;
  $('result-title').textContent = report.ok ? 'Your controls survived.' : 'Differences need a closer look.';
  $('result-summary').textContent = `${report.passed} / ${report.total} values preserved · ${report.issues.length} issues · ${report.observations.length} observations`;
  $('issues').replaceChildren();
  const allIssues = [...report.issues, ...report.observations];
  $('issue-limit').hidden = allIssues.length <= 200;
  $('issue-limit').textContent = `Showing the first 200 of ${allIssues.length} items. Download a report to read every item.`;
  for (const issue of allIssues.slice(0, 200)) {
    const card = document.createElement('article');
    card.className = 'issue';
    const heading = document.createElement('h3');
    heading.textContent = `${issue.ident} · ${issue.code} · ${issue.severity}`;
    card.append(heading);
    const description = document.createElement('p');
    description.textContent = issue.observation;
    card.append(description);
    const list = document.createElement('dl');
    for (const [label, key] of [['Expected', 'expected'], ['Type', 'expected_type'], ['Actual', 'actual'], ['Type', 'actual_type']]) {
      const term = document.createElement('dt');
      term.textContent = label;
      const definition = document.createElement('dd');
      const value = document.createElement('pre');
      value.textContent = JSON.stringify(issue[key]);
      definition.append(value);
      list.append(term, definition);
    }
    card.append(list);
    const guidance = document.createElement('p');
    guidance.textContent = issue.guidance + ' ' + issue.possible_causes.join(' ');
    card.append(guidance);
    $('issues').append(card);
  }
  $('result-title').focus();
}
$('controls').addEventListener('submit', async event => {
  event.preventDefault();
  const operation = mode;
  $('submit').disabled = true;
  $('step-make').disabled = $('step-check').disabled = true;
  $('controls').setAttribute('aria-busy', 'true');
  for (const field of $('controls').querySelectorAll('input,select,textarea')) field.disabled = true;
  if (operation === 'check') { current = null; $('results').hidden = true; }
  $('status').setAttribute('role', 'status');
  $('status').setAttribute('aria-live', 'polite');
  $('status').classList.remove('error');
  $('status').textContent = 'Working locally…';
  try {
    const options = {format: $('format').value, probe_set: $('probe-set').value, delimiter: $('delimiter').value};
    if ($('encoding').value) options.encoding = $('encoding').value;
    if ($('custom').value.trim()) options.custom_values_json = $('custom').value;
    if (operation === 'check') {
      const file = $('upload').files[0];
      if (!file) throw new Error('Choose an exported control file.');
      if (file.size > 32 * 1024 * 1024) throw new Error('The upload limit is 32 MiB.');
      options.data = await fileData(file);
      options.strict_order = $('strict-order').checked;
      options.id_column = $('id-column').value;
      options.value_column = $('value-column').value;
    }
    const response = await fetch('/api/' + operation, {method: 'POST', headers: {'Content-Type': 'application/json', 'X-RowCanary-Token': document.querySelector('meta[name="rowcanary-token"]').content}, body: JSON.stringify(options)});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'The local operation failed.');
    if (operation === 'make') {
      const data = Uint8Array.from(atob(result.data), c => c.charCodeAt(0));
      download(data, result.filename, 'application/octet-stream');
      $('status').textContent = `${result.count} controls ready. Use step 02 after your round trip.`;
    } else {
      current = result;
      showReport(result.report);
      $('status').textContent = 'Check complete. Reports are ready to download.';
    }
  } catch (error) {
    $('status').setAttribute('role', 'alert');
    $('status').setAttribute('aria-live', 'assertive');
    $('status').textContent = error.message;
    $('status').classList.add('error');
  } finally {
    $('submit').disabled = false;
    $('step-make').disabled = $('step-check').disabled = false;
    for (const field of $('controls').querySelectorAll('input,select,textarea')) field.disabled = false;
    $('id-column').disabled = $('value-column').disabled = mode === 'make';
    $('controls').setAttribute('aria-busy', 'false');
  }
});
$('download-json').addEventListener('click', () => { if (current) download(JSON.stringify(current.report, null, 2) + '\n', 'rowcanary-report.json', 'application/json'); });
$('download-html').addEventListener('click', () => { if (current) download(current.html, 'rowcanary-report.html', 'text/html'); });
setMode('make');
