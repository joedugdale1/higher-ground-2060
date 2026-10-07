/**
 * Higher Ground 2060 survey backend (Google Apps Script)
 * Receives one answer per POST, validates it on the server,
 * blocks duplicates, and appends a row to the "Responses" sheet.
 */

const SHEET_NAME = 'Responses';

// 'flag'  = record answers from a device signature already seen, but mark them possible_duplicate = yes
// 'block' = reject them outright
// 'flag' is the default because identical phones (same model, OS, language and time zone)
// can share a signature, and 'block' would wrongly turn away genuine respondents.
const DEVICE_MODE = 'flag';

const HEADERS = ['timestamp', 'respondent_id', 'plot', 'efficiency', 'community', 'safety', 'device_hash', 'possible_duplicate'];

function getSheet_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName(SHEET_NAME);
  if (!sh) sh = ss.insertSheet(SHEET_NAME);
  if (sh.getLastRow() === 0) {
    sh.appendRow(HEADERS);
    sh.setFrozenRows(1);
  }
  return sh;
}

function validate_(d) {
  if (!d || typeof d !== 'object') return 'bad_request';
  if (['present', 'future'].indexOf(d.plot) < 0) return 'bad_plot';
  if (!/^[A-Za-z0-9-]{8,64}$/.test(String(d.respondent_id || ''))) return 'bad_id';
  if (!/^[a-f0-9]{8,64}$/.test(String(d.device_hash || ''))) return 'bad_device';
  const v = [d.efficiency, d.community, d.safety];
  if (v.some(function (x) { return typeof x !== 'number' || !isFinite(x) || x < 0 || x > 1; })) return 'bad_values';
  if (Math.abs(v[0] + v[1] + v[2] - 1) > 0.001) return 'bad_sum';
  return null;
}

function doPost(e) {
  const lock = LockService.getScriptLock();
  try {
    lock.waitLock(10000); // one write at a time, so two simultaneous duplicates can't both get in
    const d = JSON.parse(e.postData.contents);
    const err = validate_(d);
    if (err) return json_({ ok: false, error: err });

    const sh = getSheet_();
    const last = sh.getLastRow();
    let idDup = false, deviceDup = false;
    if (last > 1) {
      const rows = sh.getRange(2, 1, last - 1, HEADERS.length).getValues();
      for (let i = 0; i < rows.length; i++) {
        if (rows[i][2] !== d.plot) continue;
        if (rows[i][1] === d.respondent_id) idDup = true;
        if (rows[i][6] === d.device_hash) deviceDup = true;
      }
    }
    if (idDup) return json_({ ok: false, error: 'duplicate' });
    if (deviceDup && DEVICE_MODE === 'block') return json_({ ok: false, error: 'duplicate' });

    sh.appendRow([
      new Date(), d.respondent_id, d.plot,
      d.efficiency, d.community, d.safety,
      d.device_hash, deviceDup ? 'yes' : 'no'
    ]);
    return json_({ ok: true });
  } catch (err) {
    return json_({ ok: false, error: 'server' });
  } finally {
    try { lock.releaseLock(); } catch (_) {}
  }
}

// Visiting the web app URL in a browser shows this, which confirms the deployment works.
function doGet() {
  return json_({ ok: true, status: 'running' });
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
