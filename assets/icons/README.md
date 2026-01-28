# Application Icons

This directory contains application icons for the WechatSummarizer.

## Required Files

- `app.ico` - Windows application icon (multi-resolution ICO file)
  - Recommended sizes: 16x16, 32x32, 48x48, 64x64, 128x128, 256x256

## Creating Icons

You can create the ICO file from a PNG image using various tools:

### Using ImageMagick (Command Line)

```bash
# Install ImageMagick first, then:
magick convert icon.png -define icon:auto-resize=256,128,64,48,32,16 app.ico
```

### Using Online Tools

- [ICO Convert](https://icoconvert.com/)
- [ConvertICO](https://convertico.com/)

### Design Guidelines

- Use a simple, recognizable design
- Ensure the icon looks good at small sizes (16x16)
- Use the WeChat green (#07C160) as the primary color
- Include transparency for modern Windows look
