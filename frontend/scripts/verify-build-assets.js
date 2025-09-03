#!/usr/bin/env node

/**
 * Build Asset Verification Script
 * 
 * This script verifies that all required Figma assets have been copied
 * to the dist directory during the Vite build process.
 * 
 * It checks for the existence of all assets referenced in the code
 * and reports any missing files that could cause 404 errors in production.
 */

import { existsSync, readdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Expected figma assets based on our code references
const EXPECTED_ASSETS = [
  'figmaAssets/image-1.png',       // VICE_LOGO
  'figmaAssets/image-2.png',       // BRAND_LOGO_4
  'figmaAssets/image-3.png',       // BRAND_LOGO_2
  'figmaAssets/image-4.png',       // BRAND_LOGO_1
  'figmaAssets/image-5.png',       // BRAND_LOGO_3
  'figmaAssets/image-6.png',       // ALTERNATIVE_LOGIN
  'figmaAssets/x-branded.png',     // X_BRANDED
  'figmaAssets/x1-1.gif',          // ANIMATION_GIF
  'figmaAssets/button.svg',        // BUTTONS.PRIMARY
  'figmaAssets/button-1.svg',      // Additional button
  'figmaAssets/button-2.svg',      // BUTTONS.SECONDARY
  'figmaAssets/div.svg',           // SECURITY_ICONS.SESSION
  'figmaAssets/div-1.svg',         // SECURITY_ICONS.ENCRYPTION
  'figmaAssets/div-2.svg',         // SECURITY_ICONS.ENTERPRISE
  'figmaAssets/i.svg',             // UI_ELEMENTS.ICON_1
  'figmaAssets/i-1.svg',           // UI_ELEMENTS.ICON_2
  'figmaAssets/x1-1.png',          // Additional asset
];

const DIST_DIR = join(__dirname, '../dist');
const FIGMA_ASSETS_DIR = join(DIST_DIR, 'figmaAssets');

function verifyBuildAssets() {
  console.log('🔍 Verifying build assets...\n');

  // Check if dist directory exists
  if (!existsSync(DIST_DIR)) {
    console.error('❌ Error: dist directory not found. Please run the build first.');
    process.exit(1);
  }

  // Check if figmaAssets directory exists in dist
  if (!existsSync(FIGMA_ASSETS_DIR)) {
    console.error('❌ Error: figmaAssets directory not found in dist.');
    console.error('   This suggests the public directory was not copied during build.');
    process.exit(1);
  }

  // List all actual assets in the figmaAssets directory
  const actualAssets = readdirSync(FIGMA_ASSETS_DIR);
  console.log(`📁 Found ${actualAssets.length} assets in dist/figmaAssets/`);
  
  // Check each expected asset
  const missingAssets = [];
  const foundAssets = [];
  
  for (const asset of EXPECTED_ASSETS) {
    const assetPath = join(DIST_DIR, asset);
    if (existsSync(assetPath)) {
      foundAssets.push(asset);
    } else {
      missingAssets.push(asset);
    }
  }

  // Report results
  console.log(`✅ Found assets: ${foundAssets.length}/${EXPECTED_ASSETS.length}`);
  
  if (foundAssets.length > 0) {
    console.log('\n📋 Successfully verified assets:');
    foundAssets.forEach(asset => {
      console.log(`   ✓ ${asset}`);
    });
  }

  if (missingAssets.length > 0) {
    console.log('\n⚠️  Missing assets:');
    missingAssets.forEach(asset => {
      console.log(`   ✗ ${asset}`);
    });
    console.log('\n🚨 Warning: Missing assets will result in 404 errors in production!');
    console.log('   Please ensure all required assets exist in public/figmaAssets/');
    
    // Don't fail the build for missing assets, just warn
    // In production, you might want to fail the build by uncommenting:
    // process.exit(1);
  }

  // Check for unexpected assets (assets not in our expected list)
  const expectedFilenames = EXPECTED_ASSETS.map(asset => asset.replace('figmaAssets/', ''));
  const unexpectedAssets = actualAssets.filter(asset => !expectedFilenames.includes(asset));
  
  if (unexpectedAssets.length > 0) {
    console.log('\n📦 Additional assets found (not explicitly referenced in code):');
    unexpectedAssets.forEach(asset => {
      console.log(`   ? figmaAssets/${asset}`);
    });
    console.log('   These assets are included but may not be used.');
  }

  console.log('\n🎯 Asset verification complete!');
  
  if (missingAssets.length === 0) {
    console.log('✅ All expected assets are present and accounted for.');
  } else {
    console.log('⚠️  Some assets are missing. Check warnings above.');
  }
}

// Run the verification
try {
  verifyBuildAssets();
} catch (error) {
  console.error('❌ Asset verification failed:', error.message);
  process.exit(1);
}