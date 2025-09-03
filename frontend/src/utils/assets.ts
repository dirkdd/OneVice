/**
 * Asset utility functions for handling image paths in development and production
 */

/**
 * Resolves the correct path for Figma assets based on the current environment
 * @param assetPath - The asset path relative to figmaAssets folder (e.g., 'image-1.png')
 * @returns The full path to the asset
 */
export const getFigmaAsset = (assetPath: string): string => {
  // Remove leading slash if present to avoid double slashes
  const cleanPath = assetPath.startsWith('/') ? assetPath.slice(1) : assetPath;
  
  // In Vite, assets in the public folder are served from the root
  // Both development and production should work with this approach
  return `/figmaAssets/${cleanPath}`;
};

/**
 * Validates that an asset exists (useful for development)
 * Note: This only works in development mode due to browser security restrictions
 * @param assetPath - The full asset path
 * @returns Promise that resolves to boolean indicating if asset exists
 */
export const validateAsset = async (assetPath: string): Promise<boolean> => {
  if (import.meta.env.MODE === 'production') {
    // Skip validation in production
    return true;
  }
  
  try {
    const response = await fetch(assetPath, { method: 'HEAD' });
    return response.ok;
  } catch {
    return false;
  }
};

/**
 * Common Figma assets used throughout the application
 */
export const FIGMA_ASSETS = {
  VICE_LOGO: getFigmaAsset('image-1.png'),
  BRAND_LOGO_1: getFigmaAsset('image-4.png'),
  BRAND_LOGO_2: getFigmaAsset('image-3.png'),
  BRAND_LOGO_3: getFigmaAsset('image-5.png'),
  BRAND_LOGO_4: getFigmaAsset('image-2.png'),
  SECURITY_ICONS: {
    ENTERPRISE: getFigmaAsset('div-2.svg'),
    ENCRYPTION: getFigmaAsset('div-1.svg'),
    SESSION: getFigmaAsset('div.svg'),
  },
  BUTTONS: {
    PRIMARY: getFigmaAsset('button.svg'),
    SECONDARY: getFigmaAsset('button-2.svg'),
  },
  UI_ELEMENTS: {
    ICON_1: getFigmaAsset('i.svg'),
    ICON_2: getFigmaAsset('i-1.svg'),
    X_BRANDED: getFigmaAsset('x-branded.png'),
    ALTERNATIVE_LOGIN: getFigmaAsset('image-6.png'),
    ANIMATION_GIF: getFigmaAsset('x1-1.gif'),
  }
} as const;