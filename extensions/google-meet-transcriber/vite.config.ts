import { defineConfig } from 'vite';
import { resolve } from 'path';
import fs from 'fs';

export default defineConfig({
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    },
  },
  build: {
    outDir: 'dist',
    rollupOptions: {
      input: {
        'chrome/background': resolve(__dirname, 'src/chrome/background.ts'),
        'chrome/content': resolve(__dirname, 'src/chrome/content.ts'),
        'chrome/audio-processor': resolve(__dirname, 'src/chrome/audio-processor.ts'),
        'firefox/background': resolve(__dirname, 'src/firefox/background.ts'),
        'firefox/content': resolve(__dirname, 'src/firefox/content.ts'),
        'firefox/audio-processor': resolve(__dirname, 'src/firefox/audio-processor.ts'),
      },
      output: {
        entryFileNames: '[name].js',
        chunkFileNames: '[name].js',
        assetFileNames: '[name].[ext]',
        dir: 'dist',
      },
    },
  },
  plugins: [
    {
      name: 'copy-manifests-and-assets',
      apply: 'build',
      enforce: 'post',
      async generateBundle() {
        const chromeManifest = JSON.parse(
          fs.readFileSync(resolve(__dirname, 'src/chrome/manifest.json'), 'utf-8')
        );
        const firefoxManifest = JSON.parse(
          fs.readFileSync(resolve(__dirname, 'src/firefox/manifest.json'), 'utf-8')
        );
        
        this.emitFile({
          type: 'asset',
          fileName: 'chrome/manifest.json',
          source: JSON.stringify(chromeManifest, null, 2),
        });
        
        this.emitFile({
          type: 'asset',
          fileName: 'firefox/manifest.json',
          source: JSON.stringify(firefoxManifest, null, 2),
        });

        // Copy SVG icons to both browsers
        const iconSizes = ['16', '48', '128'];
        for (const size of iconSizes) {
          const svgPath = resolve(__dirname, `src/icons/icon-${size}.svg`);
          if (fs.existsSync(svgPath)) {
            const svgContent = fs.readFileSync(svgPath, 'utf-8');
            this.emitFile({
              type: 'asset',
              fileName: `chrome/icons/icon-${size}.svg`,
              source: svgContent,
            });
            this.emitFile({
              type: 'asset',
              fileName: `firefox/icons/icon-${size}.svg`,
              source: svgContent,
            });
          }
        }

        // Copy HTML files
        const htmlFiles = ['popup.html', 'options.html', 'offscreen.html'];
        for (const htmlFile of htmlFiles) {
          const chromePath = resolve(__dirname, `src/chrome/${htmlFile}`);
          const firefoxPath = resolve(__dirname, `src/firefox/${htmlFile}`);
          
          if (fs.existsSync(chromePath)) {
            const content = fs.readFileSync(chromePath, 'utf-8');
            this.emitFile({
              type: 'asset',
              fileName: `chrome/${htmlFile}`,
              source: content,
            });
          }

          if (fs.existsSync(firefoxPath)) {
            const content = fs.readFileSync(firefoxPath, 'utf-8');
            this.emitFile({
              type: 'asset',
              fileName: `firefox/${htmlFile}`,
              source: content,
            });
          }
        }
      },
    },
  ],
});
