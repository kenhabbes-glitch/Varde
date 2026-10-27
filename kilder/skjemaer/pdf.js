// Lager schem.pdf fra schem.html (eller: node pdf.js <inn.html> <ut.pdf>). Krever playwright.
const { chromium } = require('playwright');
const { pathToFileURL } = require('url');
const path = require('path');
(async () => {
  const inn = path.resolve(process.cwd(), process.argv[2] || 'schem.html');
  const ut = path.resolve(process.cwd(), process.argv[3] || 'schem.pdf');
  const b = await chromium.launch(); const p = await b.newPage();
  await p.goto(pathToFileURL(inn).href);
  await p.pdf({ path: ut, preferCSSPageSize: true, printBackground: true });
  await b.close(); console.log('Laget ' + ut);
})();
