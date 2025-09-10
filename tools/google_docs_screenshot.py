#!/usr/bin/env python3
"""
Google Docs/Sheets/Slides Screenshot Tool

Clean, efficient screenshot generation using direct export URLs and PyMuPDF.
Based on improved approach using fitz for PDF processing.

Usage:
    python tools/google_docs_screenshot.py FILE_ID doc|sheet|slide [output_name]
"""

import sys
import os
import io
from pathlib import Path
from typing import List, Optional
import subprocess

try:
    import requests
    import fitz  # PyMuPDF
    from PIL import Image
except ImportError as e:
    print("❌ Missing dependencies. Install with:")
    print("pip install requests PyMuPDF pillow")
    sys.exit(1)


def get_access_token() -> str:
    """Get access token from service account file"""
    try:
        from google.oauth2 import service_account
        import google.auth.transport.requests
        
        # Load credentials from service account file
        credentials = service_account.Credentials.from_service_account_file(
            '/tmp/compute-sa-key.json',
            scopes=['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/presentations']
        )
        
        # Refresh the token
        request = google.auth.transport.requests.Request()
        credentials.refresh(request)
        
        return credentials.token
    except Exception as e:
        raise Exception(f"Failed to get access token from service account: {e}")


def export_to_pdf(file_id: str, file_type: str, access_token: str) -> bytes:
    """Download Google file as PDF (Docs/Sheets/Slides)."""
    if file_type == "doc":
        url = f"https://docs.google.com/document/d/{file_id}/export?format=pdf"
    elif file_type == "sheet":
        url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=pdf"
    elif file_type == "slide":
        url = f"https://docs.google.com/presentation/d/{file_id}/export/pdf"
    else:
        raise ValueError("file_type must be 'doc', 'sheet', or 'slide'")
    
    headers = {'Authorization': f'Bearer {access_token}'}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.content


def pdf_to_pngs(pdf_bytes: bytes, dpi: int = 150) -> List[Image.Image]:
    """Convert PDF bytes to a list of Pillow images."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        # Convert to pixmap with specified DPI
        mat = fitz.Matrix(dpi/72, dpi/72)  # 72 is default DPI
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        images.append(img.convert("RGBA"))
    
    doc.close()
    return images


def save_as_apng(images: List[Image.Image], out_path: str, duration: int = 3000):
    """Save list of Pillow images as APNG (animated PNG)."""
    if not images:
        raise ValueError("No images to save")
    
    images[0].save(
        out_path,
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=0,
        format="PNG"
    )


def save_as_webp(images: List[Image.Image], out_path: str, duration: int = 3000):
    """Save list of Pillow images as animated WebP."""
    if not images:
        raise ValueError("No images to save")
    
    images[0].save(
        out_path,
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=0,
        format="WEBP",
        lossless=False,
        quality=85,
        method=6
    )


def save_individual_pngs(images: List[Image.Image], output_dir: Path, base_name: str):
    """Save individual PNG files"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i, img in enumerate(images, 1):
        output_path = output_dir / f"{base_name}_page_{i:03d}.png"
        img.save(output_path, "PNG", optimize=True)
        print(f"✅ Saved page {i}: {output_path}")


def create_contact_sheet(images: List[Image.Image], output_path: Path, cols: int = 3):
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
    
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(contact_sheet)
    
    # Add title
    try:
        font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 24)
    except:
        font = ImageFont.load_default()
    
    title = f"Google Docs Export ({len(images)} pages)"
    draw.text((20, 10), title, fill='black', font=font)
    
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
        draw.text((x + 5, y + thumb_height - 25), f"Page {i+1}", fill='gray', font=font)
    
    contact_sheet.save(output_path, 'PNG', optimize=True)
    print(f"✅ Contact sheet saved: {output_path}")


def main():
    if len(sys.argv) < 3:
        print("Usage: python tools/google_docs_screenshot.py FILE_ID doc|sheet|slide [output_name]")
        print("\nExamples:")
        print("  python tools/google_docs_screenshot.py 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms sheet")
        print("  python tools/google_docs_screenshot.py your-file-id slide my_presentation")
        print("\nFile types:")
        print("  doc   - Google Docs document")
        print("  sheet - Google Sheets spreadsheet") 
        print("  slide - Google Slides presentation")
        sys.exit(1)
    
    file_id = sys.argv[1]
    file_type = sys.argv[2]
    output_name = sys.argv[3] if len(sys.argv) > 3 else f"google_{file_type}_export"
    
    if file_type not in ['doc', 'sheet', 'slide']:
        print("❌ Error: file_type must be 'doc', 'sheet', or 'slide'")
        sys.exit(1)
    
    try:
        print(f"📸 Generating screenshots for Google {file_type.title()}: {file_id}")
        
        # Get access token
        print("🔑 Getting access token...")
        access_token = get_access_token()
        
        # Export to PDF
        print("📄 Exporting to PDF...")
        pdf_bytes = export_to_pdf(file_id, file_type, access_token)
        print(f"✅ PDF exported ({len(pdf_bytes)} bytes)")
        
        # Convert to images
        print("🖼️ Converting PDF to images...")
        images = pdf_to_pngs(pdf_bytes, dpi=200)
        print(f"✅ Converted to {len(images)} images")
        
        # Create output directory
        output_dir = Path(f"{output_name}_screenshots")
        
        # Save individual PNGs
        print("💾 Saving individual PNGs...")
        save_individual_pngs(images, output_dir, output_name)
        
        # Create animated formats
        if len(images) > 1:
            print("🎬 Creating animated PNG...")
            apng_path = output_dir / f"{output_name}_animated.png"
            save_as_apng(images, str(apng_path), duration=3000)
            print(f"✅ Animated PNG created: {apng_path}")
            
            print("🎬 Creating animated WebP...")
            webp_path = output_dir / f"{output_name}_animated.webp"
            save_as_webp(images, str(webp_path), duration=3000)
            print(f"✅ Animated WebP created: {webp_path}")
        
        # Create contact sheet
        print("📋 Creating contact sheet...")
        contact_path = output_dir / f"{output_name}_contact_sheet.png"
        create_contact_sheet(images, contact_path)
        
        print(f"\n🎉 Screenshots complete! Check: {output_dir}")
        print(f"📊 Generated {len(images)} individual PNGs + animated PNG + animated WebP + contact sheet")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()