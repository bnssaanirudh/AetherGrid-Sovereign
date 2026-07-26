import puppeteer from 'puppeteer';
import { AxePuppeteer } from '@axe-core/puppeteer';
import fs from 'fs';

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 800 });

  const routes = [
    { name: 'Live_Twin_cert_success_01', path: '/' },
    { name: 'Data_Quality', path: '/data' },
    { name: 'Research_Lab', path: '/research' }
  ];

  const results = [];

  for (const route of routes) {
    console.log(`Navigating to ${route.path}...`);
    await page.goto(`http://localhost:3000${route.path}`, { waitUntil: 'domcontentloaded', timeout: 60000 });
    // wait a moment for react to render
    await new Promise(r => setTimeout(r, 2000));
    
    // Screenshot
    const screenshotPath = `../artifacts/screenshot_${route.name}.png`;
    await page.screenshot({ path: screenshotPath });
    console.log(`Saved screenshot: ${screenshotPath}`);

    // Accessibility Audit
    const axe = new AxePuppeteer(page);
    const result = await axe.analyze();
    results.push({
      route: route.path,
      violations: result.violations.map(v => ({
        id: v.id,
        impact: v.impact,
        description: v.description,
        nodes: v.nodes.length
      }))
    });
  }

  // Save Axe Report
  fs.writeFileSync('../artifacts/accessibility_report.json', JSON.stringify(results, null, 2));
  console.log('Saved accessibility report.');

  await browser.close();
})();
