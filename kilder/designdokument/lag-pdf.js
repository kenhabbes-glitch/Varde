// Lager out.pdf fra design.html. Krever playwright (se Varde-oppsett-ny-PC.docx, kapittel 7).
const { chromium } = require('playwright');
const { pathToFileURL } = require('url');
const path = require('path');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  await p.goto(pathToFileURL(path.resolve(__dirname, 'design.html')).href);
  await p.pdf({ path: path.resolve(__dirname, 'out.pdf'), preferCSSPageSize: true, printBackground: true });
  await b.close(); console.log('Laget out.pdf');
})();
