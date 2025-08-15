#!/usr/bin/env python3
"""
Screenshot Manager CLI
A command-line tool for taking website screenshots with advanced features.
"""

import os
import sys
import re
import json
import zipfile
import argparse
from datetime import datetime
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright

class ProgressBar:
    def __init__(self, total, bar_length=50):
        self.total = total
        self.current = 0
        self.bar_length = bar_length
        # Largeur maximale estimée pour effacer la ligne
        self.max_line_width = bar_length + 100 

    def update(self, current, message=""):
        self.current = current
        progress = current / self.total if self.total > 0 else 0
        filled_length = int(self.bar_length * progress)
        
        # Barre simple (sans couleurs)
        bar = "#" * filled_length + "-" * (self.bar_length - filled_length)
            
        # Animation selon le statut
        if "OK" in message:
            status = "[OK]"
        elif "ERR" in message:
            status = "[ERR]"
        elif "->" in message:
            status = "[>>]"
        else:
            status = "[..]"
            
        percent = int(progress * 100)
        
        # Tronquer le message s'il est trop long
        max_message_length = 30
        if len(message) > max_message_length:
            message = message[:max_message_length-3] + "..."
        
        # Construire la chaîne de progression
        progress_str = f'[{bar}] {percent}% {status} {message}'
        
        # Effacer toute la ligne et revenir au début, puis écrire
        # Utiliser une largeur d'effacement plus grande
        sys.stdout.write('\r' + ' ' * self.max_line_width + '\r' + progress_str)
        sys.stdout.flush()  # Force l'affichage immédiat
        
    def finish(self, message="Completed!"):
        # Effacer toute la ligne et revenir au début
        sys.stdout.write('\r' + ' ' * self.max_line_width + '\r')
        sys.stdout.flush()
        print(message)  # Message simple sans couleur et avec retour à la ligne

class ScreenshotCLI:
    def __init__(self, input_file=None, output_dir="screenshots", threads=4, quality=85, timeout=15000):
        self.input_file = input_file
        self.output_dir = output_dir
        self.threads = threads
        self.quality = quality
        self.timeout = timeout
        self.history_file = "scan_history.json"
        self.url_mapping_file = "url_mapping.json"
        self.images = []
        self.url_mapping = {}
        self.urls = []
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        self.load_url_mapping()

    def load_url_mapping(self):
        """Load URL mapping from file"""
        try:
            if os.path.exists(self.url_mapping_file):
                with open(self.url_mapping_file, 'r') as f:
                    self.url_mapping = json.load(f)
        except Exception as e:
            print(f"[!] Mapping load error: {e}")

    def save_url_mapping(self):
        """Save URL mapping to file"""
        try:
            with open(self.url_mapping_file, 'w') as f:
                json.dump(self.url_mapping, f, indent=2)
        except Exception as e:
            print(f"[!] Mapping save error: {e}")

    def read_content(self):
        """Read URLs from input file"""
        if not self.input_file:
            print("[!] No input file specified")
            return []
            
        try:
            with open(self.input_file, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            
            urls = set()
            # Extract URLs
            for match in re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', text, re.IGNORECASE):
                try:
                    parsed = urlparse(match)
                    if parsed.netloc:
                        urls.add(f"{parsed.scheme}://{parsed.netloc}")
                except:
                    pass
            return list(urls)
        except Exception as e:
            print(f"[!] Read error: {e}")
            return []

    def capture_screenshot(self, url):
        """Capture screenshot of a URL"""
        try:
            with sync_playwright() as p:
                # Optimized browser launch
                browser = p.chromium.launch(
                    headless=True,
                    args=['--disable-gpu', '--no-sandbox', '--disable-dev-shm-usage']
                )
                
                # Optimized context
                context = browser.new_context(
                    viewport={'width': 1280, 'height': 800},
                    java_script_enabled=True,
                    bypass_csp=True,
                    accept_downloads=False
                )
                
                # Block heavy resources
                def block_media(route):
                    if any(ext in route.request.url for ext in 
                          ['.mp4', '.avi', '.webm', '.mp3', '.wav', '.ogg']):
                        route.abort()
                    else:
                        route.continue_()
                
                context.route("**/*", block_media)
                
                page = context.new_page()
                
                # Navigate to URL
                page.goto(url, timeout=self.timeout)
                page.wait_for_timeout(1000)

                safe_name = re.sub(r'[^\w\-_\.]', '_', urlparse(url).netloc)
                filepath = os.path.join(self.output_dir, f"{safe_name}.jpg")
                
                # Take screenshot
                page.screenshot(
                    path=filepath,
                    type='jpeg',
                    quality=self.quality,
                    full_page=False
                )
                
                browser.close()
                return True, url, filepath
        except Exception as e:
            return False, url, str(e)

    def run_scan(self):
        """Run the scanning process"""
        print(f"[->] Reading content from: {self.input_file}")
        self.urls = self.read_content()
        total = len(self.urls)
        
        if total == 0:
            print("[!] No valid URLs found in file")
            return

        print(f"[OK] Found {total} URLs to process")
        print(f"[->] Output directory: {self.output_dir}")
        print(f"[->] Using {self.threads} threads")
        
        # Initialize progress bar
        progress_bar = ProgressBar(total)
        
        successful_captures = 0
        failed_captures = 0
        
        try:
            with ThreadPoolExecutor(max_workers=self.threads) as executor:
                # Submit all tasks
                futures = [executor.submit(self.capture_screenshot, url) for url in self.urls]
                
                # Process results as they complete
                for i, future in enumerate(as_completed(futures)):
                    try:
                        success, url, result = future.result(timeout=60)
                        if success:
                            self.images.append(result)
                            self.url_mapping[os.path.basename(result)] = url
                            successful_captures += 1
                            progress_bar.update(i + 1, f"OK {os.path.basename(result)}")
                        else:
                            failed_captures += 1
                            # Tronquer l'URL si elle est trop longue
                            short_url = url[:20] + "..." if len(url) > 20 else url
                            progress_bar.update(i + 1, f"ERR Failed: {short_url}")
                        
                    except Exception as e:
                        failed_captures += 1
                        # Tronquer le message d'erreur s'il est trop long
                        error_msg = str(e)[:20] + "..." if len(str(e)) > 20 else str(e)
                        progress_bar.update(i + 1, f"ERR Error: {error_msg}")
                        
        except Exception as e:
            print(f"[!] Scan error: {e}")
            
        # Save mappings and history
        self.save_url_mapping()
        self.save_to_history(len(self.urls), successful_captures)
        
        # Finish progress bar
        progress_bar.finish(f"[OK] {successful_captures}/{total} successful captures")
        
        print(f"[OK] Scan completed! {successful_captures}/{total} successful captures")
        print(f"[->] Results saved to: {self.output_dir}")
        
        if failed_captures > 0:
            print(f"[!] {failed_captures} captures failed")

    def save_to_history(self, total_urls, successful):
        """Save scan to history"""
        history = self.load_history()
        
        entry = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "input_file": self.input_file,
            "output_dir": self.output_dir,
            "total_urls": total_urls,
            "successful": successful
        }
        
        history.insert(0, entry)
        history = history[:20]  # Keep last 20
        
        try:
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            print(f"[!] History save error: {e}")

    def load_history(self):
        """Load scan history"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[!] History load error: {e}")
        return []

    def show_history(self):
        """Show scan history"""
        history = self.load_history()
        if not history:
            print("[!] No scan history found")
            return
            
        print("\n=== Scan History ===")
        for i, entry in enumerate(history):
            success_rate = (entry['successful'] / entry['total_urls'] * 100) if entry['total_urls'] > 0 else 0
            print(f"\n[{i+1}] {entry['date']}")
            print(f"    File: {entry['input_file']}")
            print(f"    Output: {entry['output_dir']}")
            print(f"    URLs: {entry['total_urls']}")
            print(f"    Successful: {entry['successful']} ({success_rate:.1f}%)")

    def export_to_zip(self, filename=None):
        """Export all images to ZIP"""
        if not self.images:
            # Load existing images
            if os.path.exists(self.output_dir):
                files = [f for f in os.listdir(self.output_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                self.images = [os.path.join(self.output_dir, f) for f in files]
        
        if not self.images:
            print("[!] No images to export")
            return
            
        if not filename:
            filename = f"screenshots_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            
        # Progress bar for ZIP export
        print(f"[->] Creating ZIP archive: {filename}")
        progress_bar = ProgressBar(len(self.images))
        
        try:
            with zipfile.ZipFile(filename, 'w') as zipf:
                for i, img_path in enumerate(self.images):
                    zipf.write(img_path, os.path.basename(img_path))
                    # Tronquer le nom du fichier s'il est trop long
                    short_name = os.path.basename(img_path)[:20] + "..." if len(os.path.basename(img_path)) > 20 else os.path.basename(img_path)
                    progress_bar.update(i + 1, f"Adding {short_name}")
            
            progress_bar.finish("[OK] ZIP export completed")
            print(f"[OK] ZIP export successful: {filename}")
        except Exception as e:
            progress_bar.finish("[ERR] ZIP export failed")
            print(f"[!] Error during ZIP export: {e}")

    def list_images(self):
        """List all captured images"""
        if not os.path.exists(self.output_dir):
            print("[!] Output directory does not exist")
            return
            
        files = [f for f in os.listdir(self.output_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if not files:
            print("[!] No images found")
            return
            
        print(f"\n=== Images in {self.output_dir} ===")
        for i, filename in enumerate(sorted(files)):
            filepath = os.path.join(self.output_dir, filename)
            size = os.path.getsize(filepath)
            print(f"[{i+1:2}] {filename} ({size//1024} KB)")

def main():
    parser = argparse.ArgumentParser(
        description="Screenshot Manager CLI - Capture website screenshots from URLs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python screenshot_cli.py -i urls.txt
  python screenshot_cli.py -i urls.txt -o my_captures -t 6 --quality 90
  python screenshot_cli.py --history
  python screenshot_cli.py --export my_archive.zip
  python screenshot_cli.py --list
        """
    )
    
    parser.add_argument("-i", "--input", help="Input file containing URLs")
    parser.add_argument("-o", "--output", default="screenshots", help="Output directory (default: screenshots)")
    parser.add_argument("-t", "--threads", type=int, default=4, help="Number of threads (default: 4)")
    parser.add_argument("--quality", type=int, default=85, help="JPEG quality 1-100 (default: 85)")
    parser.add_argument("--timeout", type=int, default=15000, help="Page timeout in ms (default: 15000)")
    
    parser.add_argument("--history", action="store_true", help="Show scan history")
    parser.add_argument("--export", nargs="?", const="screenshots.zip", help="Export images to ZIP")
    parser.add_argument("--list", action="store_true", help="List captured images")
    
    args = parser.parse_args()
    
    # Create CLI instance
    cli = ScreenshotCLI(
        input_file=args.input,
        output_dir=args.output,
        threads=args.threads,
        quality=args.quality,
        timeout=args.timeout
    )
    
    # Handle different modes
    if args.history:
        cli.show_history()
    elif args.export:
        cli.export_to_zip(args.export)
    elif args.list:
        cli.list_images()
    elif args.input:
        cli.run_scan()
    else:
        parser.print_help()

if __name__ == "__main__":
    # Install required packages if not present
    try:
        import playwright
    except ImportError:
        print("[!] Playwright not found. Installing...")
        os.system("pip install playwright")
        os.system("playwright install chromium")
        print("[OK] Playwright installed. Please run the script again.")
        sys.exit(1)
    
    main()