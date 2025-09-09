#!/usr/bin/env python3
"""
Google Slides Screenshot Tool for StyleStack

GitHub-compatible screenshot generator using Google Slides API as rendering engine.
Leverages existing Google Cloud authentication from CI/CD workflows.

Features:
- Upload PPTX → Google Drive → Convert to Google Slides
- Export slides as high-quality PNG images
- Works in CI/CD with service account credentials
- Clean up temporary files automatically

Environment Variables Required:
- GOOGLE_APPLICATION_CREDENTIALS: Path to service account JSON
- GCP_PROJECT_ID: Google Cloud Project ID

Usage:
    export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
    python tools/google_slides_screenshot.py input.pptx [output_dir]
"""

import os
import sys
import json
import time
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

# Check for required dependencies
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
    from google.auth.transport.requests import Request
except ImportError as e:
    print("❌ Missing Google API dependencies.")
    print("Install with: pip install google-auth google-auth-oauthlib google-api-python-client")
    sys.exit(1)

try:
    import requests
    from PIL import Image
except ImportError as e:
    print("❌ Missing additional dependencies.")
    print("Install with: pip install requests pillow")
    sys.exit(1)


class GoogleSlidesScreenshotTool:
    """Tool for generating screenshots using Google Slides API"""
    
    # Required OAuth scopes
    SCOPES = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/presentations',
        'https://www.googleapis.com/auth/presentations.readonly'
    ]
    
    def __init__(self, credentials_path: Optional[str] = None, project_id: Optional[str] = None):
        self.credentials_path = credentials_path or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        self.project_id = project_id or os.getenv('GCP_PROJECT_ID')
        
        # Initialize Google API clients
        self.credentials = self._get_credentials()
        self.drive_service = build('drive', 'v3', credentials=self.credentials)
        self.slides_service = build('slides', 'v1', credentials=self.credentials)
        
        print(f"✅ Google API authentication successful")
        if self.project_id:
            print(f"📁 Project: {self.project_id}")
        else:
            print(f"📁 Using default gcloud project")
    
    def _get_credentials(self):
        """Get credentials using gcloud CLI"""
        import subprocess
        
        try:
            # Get access token from active gcloud account
            result = subprocess.run(
                ['gcloud', 'auth', 'print-access-token'],
                capture_output=True,
                text=True,
                check=True
            )
            access_token = result.stdout.strip()
            
            # Get project ID if not set
            if not self.project_id:
                try:
                    project_result = subprocess.run(
                        ['gcloud', 'config', 'get-value', 'project'],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    self.project_id = project_result.stdout.strip()
                except:
                    pass  # Project ID is optional
            
            # Create credentials object with the token
            from google.auth.credentials import Credentials
            
            class GcloudCredentials(Credentials):
                def __init__(self, token):
                    super().__init__()
                    self.token = token
                
                def refresh(self, request):
                    # Get fresh token from gcloud
                    result = subprocess.run(
                        ['gcloud', 'auth', 'application-default', 'print-access-token'],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    self.token = result.stdout.strip()
            
            return GcloudCredentials(access_token)
            
        except subprocess.CalledProcessError as e:
            if 'application-default' in str(e):
                # Try to set up application default credentials
                try:
                    print("Setting up gcloud application default credentials...")
                    subprocess.run(['gcloud', 'auth', 'application-default', 'login'], check=True)
                    return self._get_credentials()  # Retry
                except:
                    pass
            
            raise Exception(f"gcloud authentication failed. Make sure you're logged in with: gcloud auth login")
    
    def upload_pptx_to_drive(self, pptx_path: Path) -> str:
        """Upload PPTX file to Google Drive"""
        print(f"📤 Uploading {pptx_path.name} to Google Drive...")
        
        try:
            file_metadata = {
                'name': f"StyleStack_Temp_{pptx_path.stem}_{int(time.time())}",
                'parents': []  # Upload to root folder
            }
            
            media = MediaFileUpload(
                str(pptx_path),
                mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
                resumable=True
            )
            
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,mimeType'
            ).execute()
            
            file_id = file.get('id')
            print(f"✅ Uploaded to Drive: {file.get('name')} (ID: {file_id})")
            return file_id
            
        except Exception as e:
            raise Exception(f"Failed to upload PPTX to Drive: {e}")
    
    def convert_to_google_slides(self, drive_file_id: str) -> str:
        """Convert uploaded PPTX to Google Slides format"""
        print(f"🔄 Converting to Google Slides format...")
        
        try:
            # Create a copy and convert to Google Slides format
            copy_metadata = {
                'name': f"StyleStack_Slides_Temp_{int(time.time())}",
                'mimeType': 'application/vnd.google-apps.presentation'
            }
            
            converted_file = self.drive_service.files().copy(
                fileId=drive_file_id,
                body=copy_metadata,
                fields='id,name,mimeType'
            ).execute()
            
            slides_id = converted_file.get('id')
            print(f"✅ Converted to Google Slides: {converted_file.get('name')} (ID: {slides_id})")
            
            # Delete the original PPTX from Drive
            self.drive_service.files().delete(fileId=drive_file_id).execute()
            print(f"🗑️ Cleaned up original PPTX from Drive")
            
            return slides_id
            
        except Exception as e:
            # Try to clean up original file if conversion fails
            try:
                self.drive_service.files().delete(fileId=drive_file_id).execute()
            except:
                pass
            raise Exception(f"Failed to convert to Google Slides: {e}")
    
    def get_presentation_info(self, presentation_id: str) -> Dict[str, Any]:
        """Get presentation metadata and slide information"""
        try:
            presentation = self.slides_service.presentations().get(
                presentationId=presentation_id
            ).execute()
            
            slides = presentation.get('slides', [])
            slide_info = []
            
            for i, slide in enumerate(slides):
                slide_data = {
                    'number': i + 1,
                    'object_id': slide.get('objectId'),
                    'page_elements': len(slide.get('pageElements', [])),
                    'layout_properties': slide.get('slideProperties', {}).get('layoutObjectId', 'Unknown')
                }
                slide_info.append(slide_data)
            
            return {
                'presentation_id': presentation_id,
                'title': presentation.get('title', 'Untitled'),
                'slide_count': len(slides),
                'slides': slide_info,
                'page_size': presentation.get('pageSize', {}),
                'masters': len(presentation.get('masters', [])),
                'layouts': len(presentation.get('layouts', []))
            }
            
        except Exception as e:
            raise Exception(f"Failed to get presentation info: {e}")
    
    def export_slide_as_png(self, presentation_id: str, slide_number: int, output_path: Path, 
                           width: int = 1920, height: int = 1080) -> bool:
        """Export a single slide as PNG using Drive API"""
        try:
            # Use Drive API export with custom dimensions
            export_url = f"https://docs.google.com/presentation/d/{presentation_id}/export/png"
            
            # Add parameters for slide and dimensions
            params = {
                'slide': slide_number,  # 1-indexed
                'width': width,
                'height': height
            }
            
            # Make authenticated request
            response = requests.get(
                export_url,
                params=params,
                headers={'Authorization': f'Bearer {self.credentials.token}'}
            )
            
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print(f"✅ Exported slide {slide_number}: {output_path}")
                return True
            else:
                print(f"❌ Failed to export slide {slide_number}: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error exporting slide {slide_number}: {e}")
            return False
    
    def generate_screenshots(self, pptx_path: Path, output_dir: Path, 
                           width: int = 1920, height: int = 1080) -> tuple[List[Path], Dict[str, Any]]:
        """Generate screenshots from PPTX file using Google Slides"""
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        temp_file_ids = []  # Track files to clean up
        
        try:
            # Step 1: Upload PPTX to Google Drive
            drive_file_id = self.upload_pptx_to_drive(pptx_path)
            temp_file_ids.append(drive_file_id)
            
            # Step 2: Convert to Google Slides
            slides_id = self.convert_to_google_slides(drive_file_id)
            temp_file_ids.append(slides_id)
            
            # Step 3: Get presentation information
            presentation_info = self.get_presentation_info(slides_id)
            print(f"📋 Presentation: {presentation_info['title']} ({presentation_info['slide_count']} slides)")
            
            # Step 4: Export each slide as PNG
            image_paths = []
            slide_count = presentation_info['slide_count']
            
            for slide_num in range(1, slide_count + 1):  # Google Slides uses 1-based indexing
                output_path = output_dir / f"{pptx_path.stem}_slide_{slide_num:03d}.png"
                
                if self.export_slide_as_png(slides_id, slide_num, output_path, width, height):
                    image_paths.append(output_path)
                else:
                    print(f"⚠️ Warning: Failed to export slide {slide_num}")
            
            print(f"✅ Successfully exported {len(image_paths)}/{slide_count} slides")
            
            return image_paths, presentation_info
            
        finally:
            # Cleanup: Remove temporary files from Google Drive
            for file_id in temp_file_ids:
                try:
                    self.drive_service.files().delete(fileId=file_id).execute()
                    print(f"🗑️ Cleaned up temporary file: {file_id}")
                except Exception as e:
                    print(f"⚠️ Warning: Could not clean up file {file_id}: {e}")
    
    def create_contact_sheet(self, image_paths: List[Path], output_path: Path, 
                           cols: int = 2, thumbnail_size: tuple = (400, 300)):
        """Create a contact sheet with all slides"""
        if not image_paths:
            return
        
        try:
            # Load images
            images = []
            for path in image_paths:
                try:
                    img = Image.open(path)
                    images.append(img)
                except Exception as e:
                    print(f"⚠️ Warning: Could not load {path}: {e}")
            
            if not images:
                return
            
            # Calculate grid
            rows = (len(images) + cols - 1) // cols
            
            # Create contact sheet
            thumb_width, thumb_height = thumbnail_size
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
            
            title = f"StyleStack Template Preview ({len(images)} slides) - Generated via Google Slides API"
            draw.text((20, 10), title, fill='black', font=font)
            
            # Add thumbnails
            for i, img in enumerate(images):
                row = i // cols
                col = i % cols
                
                # Resize image maintaining aspect ratio
                img.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
                
                # Calculate position
                x = col * thumb_width + (col + 1) * 20
                y = row * thumb_height + (row + 1) * 20 + 40
                
                # Center image
                img_x = x + (thumb_width - img.width) // 2
                img_y = y + (thumb_height - img.height) // 2
                
                contact_sheet.paste(img, (img_x, img_y))
                
                # Add slide number
                draw.text((x + 5, y + thumb_height - 25), f"Slide {i+1}", fill='gray', font=font)
            
            contact_sheet.save(output_path, 'PNG', optimize=True)
            print(f"✅ Contact sheet saved: {output_path}")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not create contact sheet: {e}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/google_slides_screenshot.py input.pptx [output_dir]")
        print("\nEnvironment Variables Required:")
        print("  GOOGLE_APPLICATION_CREDENTIALS - Path to service account JSON")
        print("  GCP_PROJECT_ID - Google Cloud Project ID")
        print("\nExamples:")
        print("  export GOOGLE_APPLICATION_CREDENTIALS='./service-account.json'")
        print("  python tools/google_slides_screenshot.py test.pptx")
        print("  python tools/google_slides_screenshot.py test.pptx ./screenshots")
        sys.exit(1)
    
    pptx_path = Path(sys.argv[1])
    if not pptx_path.exists():
        print(f"❌ Error: File not found: {pptx_path}")
        sys.exit(1)
    
    # Output directory
    if len(sys.argv) > 2:
        output_dir = Path(sys.argv[2])
    else:
        output_dir = Path(f"{pptx_path.stem}_gslides_screenshots")
    
    try:
        # Create screenshot tool
        tool = GoogleSlidesScreenshotTool()
        
        print(f"📸 Generating screenshots via Google Slides API: {pptx_path}")
        print(f"📁 Output directory: {output_dir}")
        
        # Generate screenshots
        image_paths, presentation_info = tool.generate_screenshots(
            pptx_path, 
            output_dir,
            width=1920,  # High quality
            height=1080
        )
        
        if image_paths:
            print(f"\n✅ Generated {len(image_paths)} slide screenshots")
            
            # Print slide information
            print(f"\n📋 Presentation Information:")
            print(f"  Title: {presentation_info['title']}")
            print(f"  Slides: {presentation_info['slide_count']}")
            print(f"  Masters: {presentation_info['masters']}")
            print(f"  Layouts: {presentation_info['layouts']}")
            
            for slide in presentation_info['slides']:
                print(f"  Slide {slide['number']}: {slide['page_elements']} elements")
            
            # Create contact sheet
            contact_sheet_path = output_dir / f"{pptx_path.stem}_contact_sheet.png"
            tool.create_contact_sheet(image_paths, contact_sheet_path)
            
            print(f"\n🎉 Screenshots complete! Check: {output_dir}")
        else:
            print(f"\n❌ No screenshots generated")
            sys.exit(1)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()