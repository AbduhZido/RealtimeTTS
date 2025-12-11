import archiver from 'archiver';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.join(__dirname, '..');

function createZip(browser) {
  return new Promise((resolve, reject) => {
    const outputPath = path.join(rootDir, `dist/google-meet-transcriber-${browser}.zip`);
    const sourceDir = path.join(rootDir, `dist/${browser}`);
    
    const output = fs.createWriteStream(outputPath);
    const archive = archiver('zip', { zlib: { level: 9 } });
    
    output.on('close', () => {
      console.log(`✓ Created ${browser} extension: ${outputPath} (${archive.pointer()} bytes)`);
      resolve();
    });
    
    archive.on('error', (err) => {
      reject(err);
    });
    
    archive.pipe(output);
    archive.directory(sourceDir, 'dist/' + browser);
    archive.finalize();
  });
}

async function main() {
  try {
    const browser = process.argv[2];
    
    if (browser && !['chrome', 'firefox'].includes(browser)) {
      console.error(`Invalid browser: ${browser}. Must be 'chrome' or 'firefox'.`);
      process.exit(1);
    }
    
    if (browser) {
      await createZip(browser);
      console.log(`\n✓ ${browser} extension packaged successfully!`);
    } else {
      await createZip('chrome');
      await createZip('firefox');
      console.log('\n✓ All extensions packaged successfully!');
    }
    
    process.exit(0);
  } catch (error) {
    console.error('Failed to pack extensions:', error);
    process.exit(1);
  }
}

main();
