# operator/vision.py
"""
Dmitry Vision System - Screen Perception

Gives Dmitry "eyes" to see the screen and make context-aware decisions.
Captures screenshots and extracts visible elements.
"""

import os
import io
import base64
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

try:
    import mss
    HAS_MSS = True
except ImportError:
    HAS_MSS = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


@dataclass
class ScreenCapture:
    """A captured screenshot."""
    image_data: bytes
    width: int
    height: int
    timestamp: datetime
    monitor: int = 0  # Which monitor was captured
    
    def save(self, path: str):
        """Save screenshot to file."""
        with open(path, "wb") as f:
            f.write(self.image_data)
    
    def to_base64(self) -> str:
        """Convert to base64 for API transmission."""
        return base64.b64encode(self.image_data).decode("utf-8")


@dataclass 
class VisibleElement:
    """A UI element detected on screen."""
    type: str  # button, text, input, icon, window
    text: Optional[str]
    bounds: Dict[str, int]  # x, y, width, height
    confidence: float = 1.0


class VisionSystem:
    """
    Screen capture and perception system.
    
    Features:
    - Full screen capture
    - Active window capture
    - Region capture
    - Element detection (requires vision model integration)
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize vision system.
        
        Args:
            cache_dir: Directory to cache screenshots (optional)
        """
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        if not HAS_MSS:
            print("⚠️ mss not installed. Run: pip install mss")
        if not HAS_PIL:
            print("⚠️ Pillow not installed. Run: pip install Pillow")
    
    def capture_screen(self, monitor: int = 0) -> Optional[ScreenCapture]:
        """
        Capture the entire screen.
        
        Args:
            monitor: Monitor index (0 = all, 1 = first, etc.)
            
        Returns:
            ScreenCapture object or None if failed
        """
        if not HAS_MSS:
            return None
        
        try:
            with mss.mss() as sct:
                mon = sct.monitors[monitor]
                screenshot = sct.grab(mon)
                
                # Convert to PNG bytes
                png_data = mss.tools.to_png(screenshot.rgb, screenshot.size)
                
                return ScreenCapture(
                    image_data=png_data,
                    width=screenshot.width,
                    height=screenshot.height,
                    timestamp=datetime.now(),
                    monitor=monitor,
                )
        except Exception as e:
            print(f"Screen capture failed: {e}")
            return None
    
    def capture_region(
        self, 
        x: int, 
        y: int, 
        width: int, 
        height: int
    ) -> Optional[ScreenCapture]:
        """
        Capture a specific region of the screen.
        
        Args:
            x, y: Top-left corner
            width, height: Size of region
        """
        if not HAS_MSS:
            return None
        
        try:
            with mss.mss() as sct:
                region = {"left": x, "top": y, "width": width, "height": height}
                screenshot = sct.grab(region)
                png_data = mss.tools.to_png(screenshot.rgb, screenshot.size)
                
                return ScreenCapture(
                    image_data=png_data,
                    width=width,
                    height=height,
                    timestamp=datetime.now(),
                )
        except Exception as e:
            print(f"Region capture failed: {e}")
            return None
    
    def capture_and_save(
        self, 
        filename: Optional[str] = None,
        monitor: int = 0
    ) -> Optional[str]:
        """
        Capture screen and save to file.
        
        Returns:
            Path to saved file or None
        """
        capture = self.capture_screen(monitor)
        if not capture:
            return None
        
        if not filename:
            timestamp = capture.timestamp.strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
        
        if self.cache_dir:
            path = self.cache_dir / filename
        else:
            path = Path(filename)
        
        capture.save(str(path))
        return str(path)
    
    def get_screen_info(self) -> List[Dict[str, Any]]:
        """Get information about available monitors."""
        if not HAS_MSS:
            return []
        
        try:
            with mss.mss() as sct:
                return [
                    {
                        "index": i,
                        "left": m["left"],
                        "top": m["top"],
                        "width": m["width"],
                        "height": m["height"],
                    }
                    for i, m in enumerate(sct.monitors)
                ]
        except:
            return []
    
    def capture_for_llm(self, monitor: int = 0) -> Optional[Dict[str, Any]]:
        """
        Capture screen in a format ready for LLM vision API.
        
        Returns:
            Dict with image data and metadata
        """
        capture = self.capture_screen(monitor)
        if not capture:
            return None
        
        return {
            "type": "image",
            "data": capture.to_base64(),
            "width": capture.width,
            "height": capture.height,
            "format": "png",
        }
    
    # ========== ELEMENT DETECTION (PLACEHOLDER) ==========
    # These would integrate with a vision model (GPT-4V, Claude, etc.)
    
    def detect_elements(
        self, 
        capture: ScreenCapture,
        element_types: Optional[List[str]] = None
    ) -> List[VisibleElement]:
        """
        Detect UI elements in a screenshot.
        
        NOTE: This is a placeholder. Real implementation would:
        1. Send image to vision model
        2. Parse response for detected elements
        3. Return structured data
        
        Args:
            capture: Screenshot to analyze
            element_types: Types to detect (button, text, etc.)
        """
        # Placeholder - would integrate with vision API
        return []
    
    def find_element(
        self, 
        description: str,
        capture: Optional[ScreenCapture] = None
    ) -> Optional[VisibleElement]:
        """
        Find a specific element by description.
        
        Example:
            find_element("the blue Submit button")
            find_element("the error message")
        
        NOTE: Placeholder for vision model integration.
        """
        if capture is None:
            capture = self.capture_screen()
        
        if capture is None:
            return None
        
        # Placeholder - would use vision model to locate element
        return None
    
    def get_screen_context(self) -> Dict[str, Any]:
        """
        Get a summary of what's visible on screen.
        
        Returns structured data about:
        - Visible windows
        - Active app
        - Notable elements
        
        NOTE: Placeholder for vision model integration.
        """
        # Placeholder - would use vision model
        return {
            "status": "vision_model_not_integrated",
            "message": "Screen context requires vision model integration"
        }
