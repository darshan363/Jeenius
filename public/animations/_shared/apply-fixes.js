/**
 * Patch script to improve text overflow and responsiveness
 * Run this with Node.js to update all animation HTML files
 * Preserves all existing colors, fonts, and design system
 */

const fs = require('fs');
const path = require('path');

// CSS improvements to inject (preserves design system completely)
const CSS_IMPROVEMENTS = `
/* JEENIUS RESPONSIVE IMPROVEMENTS - Preserves all design tokens */
#fx{font:600 14px/1.65 Goldman,sans-serif;background:#e6eeff;padding:10px 12px;margin-top:8px;border-left:4px solid #013062;overflow-wrap:anywhere;word-break:break-word;hyphens:auto}
#ro b{font-size:13px;text-align:right;word-break:break-word;overflow-wrap:anywhere;max-width:58%}
#ro div{display:flex;justify-content:space-between;gap:10px;border-bottom:1px dashed rgba(1,48,98,.4);padding:3px 0;font-size:13px}
p{max-width:70ch;overflow-wrap:break-word}
h1{font-size:clamp(20px,4.5vw,34px);letter-spacing:.02em;overflow-wrap:break-word}
canvas{width:100%;aspect-ratio:16/9;display:block;touch-action:none;border:1px solid #013062;background:#fff;max-width:100%;height:auto}
.row label{display:flex;justify-content:space-between;gap:8px;font-size:13px;align-items:baseline;flex-wrap:wrap}
@media(max-width:860px){main{grid-template-columns:minmax(0,1fr)}body{padding:12px 14px 24px}.ch{padding:12px}#ro b{max-width:52%;font-size:12px}#ro div{font-size:12px}#fx{font-size:13px;line-height:1.7}h1{font-size:clamp(18px,5vw,28px)}h2{font-size:12px}}
@media(max-width:480px){body{padding:10px 10px 20px}h1{font-size:clamp(17px,6vw,24px)}#ro b{max-width:48%;font-size:11px}#ro div{font-size:11px;gap:6px}#fx{font-size:12px;line-height:1.75}}
@media(prefers-reduced-motion:reduce){*{animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important}}
`.trim();

function patchCanvasAnimation(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');

  // Check if already patched
  if (content.includes('JEENIUS RESPONSIVE IMPROVEMENTS')) {
    console.log(`  ✓ Already patched: ${path.basename(path.dirname(filePath))}`);
    return false;
  }

  // Find the media query and inject improvements before </style>
  const mediaQueryMatch = content.match(/@media\(max-width:860px\)\{main\{grid-template-columns:minmax\(0,1fr\)\}\}/);

  if (mediaQueryMatch) {
    // Insert improvements right after the existing media query
    const insertionPoint = content.indexOf(mediaQueryMatch[0]) + mediaQueryMatch[0].length;
    const beforeStyle = content.substring(0, insertionPoint);
    const afterStyle = content.substring(insertionPoint);

    content = beforeStyle + '\n' + CSS_IMPROVEMENTS + afterStyle;
    fs.writeFileSync(filePath, content, 'utf8');
    console.log(`  ✓ Patched: ${path.basename(path.dirname(filePath))}`);
    return true;
  }

  console.log(`  ⚠ Could not patch (no match): ${path.basename(path.dirname(filePath))}`);
  return false;
}

function patchLessonEngineAnimation(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');

  // Check if already patched
  if (content.includes('JEENIUS RESPONSIVE IMPROVEMENTS')) {
    console.log(`  ✓ Already patched: ${path.basename(path.dirname(filePath))}`);
    return false;
  }

  // Inject before </head>
  if (content.includes('</head>')) {
    const injection = `<style>${CSS_IMPROVEMENTS}</style>\n</head>`;
    content = content.replace('</head>', injection);
    fs.writeFileSync(filePath, content, 'utf8');
    console.log(`  ✓ Patched: ${path.basename(path.dirname(filePath))}`);
    return true;
  }

  console.log(`  ⚠ Could not patch: ${path.basename(path.dirname(filePath))}`);
  return false;
}

function patchLabJsAnimation(filePath) {
  // Lab.js animations are simpler - they use lab.js styling
  // Just ensure the shared lab.js has good responsive CSS
  console.log(`  → Lab.js animation (styling in lab.js): ${path.basename(path.dirname(filePath))}`);
  return false;
}

// Main execution
console.log('\n🎨 JEENIUS Animation Responsive Patcher');
console.log('========================================\n');

const animationsDir = __dirname.replace('_shared', '');
const dirs = fs.readdirSync(animationsDir)
  .filter(name => /^\d{2}-/.test(name))
  .sort();

let canvasPatched = 0;
let lessonPatched = 0;
let labSkipped = 0;

console.log('Processing canvas-based animations (01-40)...');
for (let i = 0; i < 40 && i < dirs.length; i++) {
  const dir = dirs[i];
  const indexPath = path.join(animationsDir, dir, 'index.html');
  if (fs.existsSync(indexPath)) {
    if (patchCanvasAnimation(indexPath)) canvasPatched++;
  }
}

console.log('\nProcessing Lab.js animations (41-60)...');
for (let i = 40; i < 60 && i < dirs.length; i++) {
  const dir = dirs[i];
  const indexPath = path.join(animationsDir, dir, 'index.html');
  if (fs.existsSync(indexPath)) {
    patchLabJsAnimation(indexPath);
    labSkipped++;
  }
}

console.log('\nProcessing lesson-engine animations (61-78)...');
for (let i = 60; i < dirs.length; i++) {
  const dir = dirs[i];
  const indexPath = path.join(animationsDir, dir, 'index.html');
  if (fs.existsSync(indexPath)) {
    if (patchLessonEngineAnimation(indexPath)) lessonPatched++;
  }
}

console.log('\n========================================');
console.log('📊 Summary:');
console.log(`  Canvas animations patched: ${canvasPatched}`);
console.log(`  Lesson-engine patched: ${lessonPatched}`);
console.log(`  Lab.js animations (use shared CSS): ${labSkipped}`);
console.log(`  Total improvements applied: ${canvasPatched + lessonPatched}`);
console.log('\n✅ Done! All design tokens preserved.\n');
