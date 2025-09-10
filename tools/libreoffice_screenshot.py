#!/usr/bin/env python3
"""
LibreOffice Headless Screenshot Tool

GitHub-native screenshot generation using LibreOffice headless mode.
No Google Drive storage - everything stays in GitHub.

Usage:
    python tools/libreoffice_screenshot.py template.pptx
    python tools/libreoffice_screenshot.py *.pptx
"""

import os
import sys
import subprocess
import io
from pathlib import Path
from typing import List

try:
    from PIL import Image, ImageDraw, ImageFont
    import fitz  # PyMuPDF
except ImportError as e:
    print("❌ Missing dependencies. Install with:")
    print("pip install pillow PyMuPDF")
    sys.exit(1)

def find_libreoffice() -> str:
    """Find LibreOffice executable on different platforms"""
    # Common paths for different OS
    possible_paths = [
        'libreoffice',  # Linux/Ubuntu (apt package)
        '/usr/bin/libreoffice',  # Linux
        '/Applications/LibreOffice.app/Contents/MacOS/soffice',  # macOS
        'C:\\Program Files\\LibreOffice\\program\\soffice.exe',  # Windows
        'C:\\Program Files (x86)\\LibreOffice\\program\\soffice.exe',  # Windows 32-bit
    ]
    
    for path in possible_paths:
        if os.path.exists(path) or subprocess.run(['which', path], capture_output=True).returncode == 0:
            return path
    
    raise FileNotFoundError("LibreOffice not found. Install LibreOffice or add it to PATH.")

def create_contact_sheet(images: List[Image.Image], output_path: Path, cols: int = 3, title: str = None):
    """Create a contact sheet with all pages"""
    if not images:
        return
    
    # Calculate grid
    rows = (len(images) + cols - 1) // cols
    
    # Thumbnail size
    thumb_width, thumb_height = 300, 400
    
    # Create contact sheet
    contact_width = cols * thumb_width + (cols + 1) * 20
    contact_height = rows * thumb_height + (rows + 1) * 20 + 40
    
    contact_sheet = Image.new('RGB', (contact_width, contact_height), 'white')
    
    draw = ImageDraw.Draw(contact_sheet)
    
    # Add title
    try:
        # Try different font paths for cross-platform compatibility
        font_paths = [
            '/System/Library/Fonts/Helvetica.ttc',  # macOS
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',  # Ubuntu
            'C:\\Windows\\Fonts\\arial.ttf',  # Windows
        ]
        font = None
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, 24)
                break
            except:
                continue
        if font is None:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    display_title = title or f"Office Document Export ({len(images)} pages)"
    draw.text((20, 10), display_title, fill='black', font=font)
    
    # Add thumbnails
    for i, img in enumerate(images):
        row = i // cols
        col = i % cols
        
        # Resize image maintaining aspect ratio
        img_copy = img.copy()
        img_copy.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)
        
        # Calculate position
        x = col * thumb_width + (col + 1) * 20
        y = row * thumb_height + (row + 1) * 20 + 40
        
        # Center image in thumbnail area
        img_x = x + (thumb_width - img_copy.width) // 2
        img_y = y + (thumb_height - img_copy.height) // 2
        
        contact_sheet.paste(img_copy, (img_x, img_y))
        
        # Add page number
        try:
            page_font = ImageFont.truetype(font_paths[0], 16) if font_paths else ImageFont.load_default()
        except:
            page_font = ImageFont.load_default()
        draw.text((x + 5, y + thumb_height - 25), f"Page {i+1}", fill='gray', font=page_font)
    
    contact_sheet.save(output_path, 'PNG', optimize=True)
    print(f"✅ Contact sheet saved: {output_path}")

def convert_office_to_screenshots(file_path: str, output_dir: Path = None, dpi: int = 300) -> bool:
    """Convert Office documents (PPTX, DOCX, XLSX) to screenshots using LibreOffice headless"""
    office_file = Path(file_path)
    if not office_file.exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    # Determine file type
    file_ext = office_file.suffix.lower()
    file_types = {
        '.pptx': '📊 PowerPoint Presentation',
        '.potx': '📊 PowerPoint Template', 
        '.docx': '📄 Word Document',
        '.dotx': '📄 Word Template',
        '.xlsx': '📈 Excel Spreadsheet',
        '.xltx': '📈 Excel Template'
    }
    
    file_type_name = file_types.get(file_ext, f'📁 Office Document ({file_ext})')
    print(f"📸 Processing: {office_file.name} ({file_type_name})")
    
    # Create output directory
    if output_dir is None:
        output_dir = Path(f"{office_file.stem}_screenshots")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Find LibreOffice executable
    try:
        libreoffice_cmd = find_libreoffice()
        print(f"🔧 Using LibreOffice: {libreoffice_cmd}")
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return False
    
    # Convert Office document to PDF using LibreOffice headless
    pdf_path = output_dir / f"{office_file.stem}.pdf"
    print(f"📄 Converting {file_type_name} to PDF with LibreOffice...")
    
    try:
        # Use absolute paths to avoid issues
        result = subprocess.run([
            libreoffice_cmd, '--headless', '--convert-to', 'pdf',
            '--outdir', str(output_dir.absolute()), 
            str(office_file.absolute())
        ], capture_output=True, text=True, check=True, timeout=60)
        
        print(f"✅ PDF created: {pdf_path}")
        if result.stdout:
            print(f"LibreOffice output: {result.stdout}")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ LibreOffice conversion failed: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        print("❌ LibreOffice conversion timed out")
        return False
    
    # Verify PDF was created
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return False
    
    # Convert PDF to images using PyMuPDF
    print("🖼️ Converting PDF to PNG images...")
    try:
        doc = fitz.open(str(pdf_path))
        images = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            # High DPI for quality screenshots
            mat = fitz.Matrix(dpi/72, dpi/72)  # Convert DPI to scale factor
            pix = page.get_pixmap(matrix=mat)
            
            # Determine naming convention based on file type
            if file_ext in ['.pptx', '.potx']:
                page_prefix = "slide"
                page_label = "slide"
            elif file_ext in ['.docx', '.dotx']:
                page_prefix = "page"
                page_label = "page"
            elif file_ext in ['.xlsx', '.xltx']:
                page_prefix = "sheet"
                page_label = "sheet"
            else:
                page_prefix = "page"
                page_label = "page"
            
            # Save individual PNG
            png_path = output_dir / f"{page_prefix}_{page_num+1:03d}.png"
            pix.save(str(png_path))
            print(f"✅ Saved {page_label} {page_num+1}: {png_path}")
            
            # Convert to PIL Image for animation
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            images.append(img.convert("RGB"))
        
        doc.close()
        
    except Exception as e:
        print(f"❌ PDF to PNG conversion failed: {e}")
        return False
    
    # Create animated formats if multiple pages/slides
    if len(images) > 1:
        # Determine duration based on file type
        page_duration = 3000 if file_ext in ['.pptx', '.potx'] else 2000  # Slides: 3s, Docs/Sheets: 2s
        
        # Animated PNG
        apng_path = output_dir / f"{office_file.stem}_animated.png"
        print(f"🎬 Creating animated PNG: {apng_path}")
        try:
            images[0].save(
                str(apng_path),
                save_all=True,
                append_images=images[1:],
                duration=page_duration,
                loop=0,
                format="PNG"
            )
            print(f"✅ Animated PNG created: {apng_path}")
        except Exception as e:
            print(f"⚠️ Animated PNG creation failed: {e}")
        
        # Animated WebP
        webp_path = output_dir / f"{office_file.stem}_animated.webp"
        print(f"🎬 Creating animated WebP: {webp_path}")
        try:
            images[0].save(
                str(webp_path),
                save_all=True,
                append_images=images[1:],
                duration=page_duration,
                loop=0,
                format="WEBP",
                lossless=False,
                quality=85,
                method=6
            )
            print(f"✅ Animated WebP created: {webp_path}")
        except Exception as e:
            print(f"⚠️ Animated WebP creation failed: {e}")
    else:
        print("ℹ️ Single page - no animated formats created")
    
    # Create contact sheet
    if images:
        contact_path = output_dir / f"{office_file.stem}_contact_sheet.png"
        print(f"📋 Creating contact sheet: {contact_path}")
        try:
            create_contact_sheet(images, contact_path, title=f"{file_type_name} ({len(images)} pages)")
        except Exception as e:
            print(f"⚠️ Contact sheet creation failed: {e}")
    
    # Cleanup PDF
    try:
        pdf_path.unlink()
        print("🗑️ Cleaned up temporary PDF")
    except:
        pass
    
    print(f"🎉 Generated {len(images)} screenshots + animated formats + contact sheet")
    return True

def show_help():
    """Show help message"""
    print("LibreOffice Headless Screenshot Tool")
    print("=" * 40)
    print("GitHub-native screenshot generation using LibreOffice headless mode.")
    print("No Google Drive storage - everything stays in GitHub.")
    print()
    print("Usage: python tools/libreoffice_screenshot.py [OPTIONS] FILE [FILE2 ...]")
    print()
    print("Options:")
    print("  -h, --help     Show this help message")
    print()
    print("Supported formats: .pptx, .potx, .docx, .dotx, .xlsx, .xltx")
    print()
    print("Examples:")
    print("  python tools/libreoffice_screenshot.py template.pptx")
    print("  python tools/libreoffice_screenshot.py document.docx")
    print("  python tools/libreoffice_screenshot.py spreadsheet.xlsx")
    print("  python tools/libreoffice_screenshot.py *.pptx *.docx *.xlsx")
    print()
    print("Output:")
    print("  • Individual PNG files (slide_001.png, page_001.png, sheet_001.png)")
    print("  • Animated PNG (APNG) for multi-page documents")
    print("  • Animated WebP for efficient web delivery")
    print("  • Contact sheet with thumbnail overview")

def main():
    # Check for help flags
    if len(sys.argv) < 2 or '--help' in sys.argv or '-h' in sys.argv:
        show_help()
        sys.exit(0 if ('--help' in sys.argv or '-h' in sys.argv) else 1)
    
    files = sys.argv[1:]
    success_count = 0
    
    print("🧪 LibreOffice Headless Screenshot Tool")
    print("=" * 50)
    
    for file_path in files:
        # Handle wildcards by expanding them
        if '*' in file_path or '?' in file_path:
            from glob import glob
            expanded_files = glob(file_path)
            if not expanded_files:
                print(f"❌ No files found matching: {file_path}")
                continue
            files.extend(expanded_files)
            continue
        
        if os.path.exists(file_path.strip()):
            print(f"\n" + "="*50)
            if convert_office_to_screenshots(file_path.strip()):
                success_count += 1
        else:
            print(f"❌ File not found: {file_path}")
    
    print(f"\n✅ Successfully processed {success_count} files")
    
    if success_count > 0:
        print("\n📁 Screenshot directories created:")
        for dir_path in Path(".").glob("*_screenshots"):
            if dir_path.is_dir():
                files_count = len(list(dir_path.glob("*")))
                print(f"  - {dir_path} ({files_count} files)")

if __name__ == "__main__":
    main()