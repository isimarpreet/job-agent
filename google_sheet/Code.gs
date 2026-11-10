/**
 * Job Tracker sync. Paste this into your Google Sheet: Extensions > Apps Script.
 *
 * The job agent sends every row of tracker.csv here. This script adds new jobs,
 * updates changed ones (matched by link), and never deletes rows. It also sets up
 * the header, filter, status dropdown, colours and a Summary tab.
 *
 * Do not paste this template directly. Run `venv/bin/python google_sheet/sync.py setup`
 * and paste google_sheet/Code_to_paste.gs instead, which has your secret key filled in.
 */

const TOKEN = '__TOKEN__';
const STATUSES = ['shortlisted', 'applied', 'waiting_for_you', 'skipped'];
const STATUS_COLOURS = { applied: '#c8e6c9', waiting_for_you: '#fff59d', skipped: '#e0e0e0' };

function doGet() {
  return reply({ ok: true, message: 'Job Tracker sync is running.' });
}

function doPost(e) {
  try {
    const body = JSON.parse(e.postData.contents);
    if (body.token !== TOKEN) {
      return reply({ ok: false, error: 'Wrong secret key.' });
    }
    const lock = LockService.getScriptLock();
    lock.waitLock(30000);
    try {
      return reply(syncRows(body.columns, body.rows));
    } finally {
      lock.releaseLock();
    }
  } catch (error) {
    return reply({ ok: false, error: String(error) });
  }
}

function reply(result) {
  return ContentService.createTextOutput(JSON.stringify(result))
    .setMimeType(ContentService.MimeType.JSON);
}

function syncRows(columns, rows) {
  const book = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = book.getSheetByName('Jobs');
  if (!sheet) {
    sheet = book.insertSheet('Jobs', 0);
  }

  // Keep existing columns in place and add any new ones at the end.
  const header = sheet.getLastRow() > 0
    ? sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0].map(String)
    : [];
  columns.forEach(function (column) {
    if (header.indexOf(column) === -1) header.push(column);
  });
  sheet.getRange(1, 1, 1, header.length).setValues([header]);
  if (sheet.getFrozenRows() === 0) {
    setUp(book, sheet, header);
  }

  const lastRow = sheet.getLastRow();
  const existing = lastRow > 1
    ? sheet.getRange(2, 1, lastRow - 1, header.length).getValues()
    : [];
  const positions = {};
  existing.forEach(function (row, i) {
    positions[keyOf(header, row)] = i;
  });

  let updated = 0;
  const added = [];
  rows.forEach(function (source) {
    const values = header.map(function (column) { return cellValue(column, source[column]); });
    const key = keyOf(header, values);
    if (key in positions) {
      const i = positions[key];
      if (i >= 0 && existing[i].map(String).join('\u0001') !== values.map(String).join('\u0001')) {
        existing[i] = values;
        updated += 1;
      }
    } else {
      added.push(values);
      positions[key] = -1;
    }
  });

  if (updated > 0) {
    writeBlock(sheet, 2, header, existing);
  }
  if (added.length > 0) {
    writeBlock(sheet, lastRow + 1, header, added);
  }
  return { ok: true, added: added.length, updated: updated, total: existing.length + added.length };
}

function keyOf(header, row) {
  const link = String(row[header.indexOf('link')] || '').trim();
  if (link) return link;
  return String(row[header.indexOf('job')]) + '|' + String(row[header.indexOf('company')]);
}

function cellValue(column, value) {
  const text = value === null || value === undefined ? '' : String(value);
  if (column === 'score' && text !== '' && !isNaN(Number(text))) return Number(text);
  // Stop job text from being treated as a formula.
  if (/^[=+\-@]/.test(text)) return "'" + text;
  return text;
}

function writeBlock(sheet, startRow, header, values) {
  const needed = startRow + values.length - 1;
  if (needed > sheet.getMaxRows()) {
    sheet.insertRowsAfter(sheet.getMaxRows(), needed - sheet.getMaxRows());
  }
  const range = sheet.getRange(startRow, 1, values.length, header.length);
  // Plain text everywhere except score, so dates and numbers stay exactly as sent.
  range.setNumberFormat('@');
  const scoreColumn = header.indexOf('score');
  if (scoreColumn >= 0) {
    sheet.getRange(startRow, scoreColumn + 1, values.length, 1).setNumberFormat('0');
  }
  range.setValues(values);
}

function letter(columnNumber) {
  let text = '';
  while (columnNumber > 0) {
    const remainder = (columnNumber - 1) % 26;
    text = String.fromCharCode(65 + remainder) + text;
    columnNumber = Math.floor((columnNumber - 1) / 26);
  }
  return text;
}

function setUp(book, sheet, header) {
  const width = header.length;
  const rows = sheet.getMaxRows();

  const top = sheet.getRange(1, 1, 1, width);
  top.setFontWeight('bold').setBackground('#1f3864').setFontColor('#ffffff');
  sheet.setFrozenRows(1);
  if (!sheet.getFilter()) {
    sheet.getRange(1, 1, rows, width).createFilter();
  }

  const widths = { job: 280, company: 170, location: 150, missing_skills: 320, link: 260, notes: 260 };
  header.forEach(function (column, i) {
    sheet.setColumnWidth(i + 1, widths[column] || 120);
    if (column === 'job' || column === 'missing_skills' || column === 'notes') {
      sheet.getRange(2, i + 1, rows - 1, 1).setWrap(true);
    }
  });

  const statusColumn = header.indexOf('status') + 1;
  if (statusColumn > 0) {
    const statusRange = sheet.getRange(2, statusColumn, rows - 1, 1);
    statusRange.setDataValidation(
      SpreadsheetApp.newDataValidation().requireValueInList(STATUSES, true).build()
    );
    const rowRange = sheet.getRange(2, 1, rows - 1, width);
    const column = letter(statusColumn);
    const rules = Object.keys(STATUS_COLOURS).map(function (status) {
      return SpreadsheetApp.newConditionalFormatRule()
        .whenFormulaSatisfied('=$' + column + '2="' + status + '"')
        .setBackground(STATUS_COLOURS[status])
        .setRanges([rowRange])
        .build();
    });
    sheet.setConditionalFormatRules(rules);
  }

  const blank = book.getSheetByName('Sheet1');
  if (blank && blank.getLastRow() === 0 && book.getSheets().length > 1) {
    book.deleteSheet(blank);
  }
  addSummary(book, header);
}

function addSummary(book, header) {
  let summary = book.getSheetByName('Summary');
  if (!summary) summary = book.insertSheet('Summary');
  summary.clear();

  const statusColumn = letter(header.indexOf('status') + 1);
  const dateColumn = letter(header.indexOf('date_found') + 1);
  const appliedColumn = letter(header.indexOf('applied_on') + 1);
  const jobColumn = letter(header.indexOf('job') + 1);
  const lastColumn = letter(header.length);

  summary.getRange('A1:B1').setValues([['Status', 'Jobs']]);
  STATUSES.forEach(function (status, i) {
    summary.getRange(i + 2, 1).setValue(status);
    summary.getRange(i + 2, 2).setFormula('=COUNTIF(Jobs!' + statusColumn + ':' + statusColumn + ',A' + (i + 2) + ')');
  });
  const totalRow = STATUSES.length + 2;
  summary.getRange(totalRow, 1).setValue('Total');
  summary.getRange(totalRow, 2).setFormula('=COUNTA(Jobs!' + jobColumn + ':' + jobColumn + ')-1');

  summary.getRange('D1').setFormula(
    '=QUERY(Jobs!A:' + lastColumn + ',"select ' + dateColumn + ', count(' + jobColumn + ') where ' +
    dateColumn + ' is not null group by ' + dateColumn + ' label ' + dateColumn + " 'Date found', count(" +
    jobColumn + ") 'Jobs found'\",1)"
  );
  summary.getRange('G1').setFormula(
    '=QUERY(Jobs!A:' + lastColumn + ',"select ' + appliedColumn + ', count(' + jobColumn + ') where ' +
    appliedColumn + " is not null and " + appliedColumn + " <> '' group by " + appliedColumn + ' label ' +
    appliedColumn + " 'Applied on', count(" + jobColumn + ") 'Applications'\",1)"
  );
  summary.getRange('A1:H1').setFontWeight('bold');
  summary.setFrozenRows(1);
}
