// Render graphics.html to a transparent PNG sequence.
// usage: node render.js <outDir> [workers] [onlyTimes,comma,separated]
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const outDir = process.argv[2];
const workers = Number(process.argv[3] || 4);
const only = process.argv[4] ? process.argv[4].split(',').map(Number) : null;
const timeline = JSON.parse(fs.readFileSync(path.join(__dirname, 'timeline.json'), 'utf8'));
fs.mkdirSync(outDir, { recursive: true });

(async () => {
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const nFrames = Math.round(timeline.duration * timeline.fps);
  const jobs = only ? only.map(t => ({ t, name: `t_${t.toFixed(2)}.png` }))
    : [...Array(nFrames).keys()].map(i => ({ t: i / timeline.fps, name: `f_${String(i).padStart(5, '0')}.png` }));
  let next = 0;
  const t0 = Date.now();
  await Promise.all([...Array(workers)].map(async () => {
    const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
    await page.goto('file://' + path.join(__dirname, 'graphics.html'));
    await page.evaluate(tl => init(tl), timeline);
    while (next < jobs.length) {
      const job = jobs[next++];
      const data = await page.evaluate(t => { draw(t); return document.getElementById('c').toDataURL('image/png'); }, job.t);
      fs.writeFileSync(path.join(outDir, job.name), Buffer.from(data.split(',')[1], 'base64'));
      if (next % 100 === 0) console.log(`${next}/${jobs.length} ${((Date.now() - t0) / 1000).toFixed(0)}s`);
    }
  }));
  await browser.close();
})();
