# core/enhanced_vision.py
"""
Enhanced Vision System with OCR and UI Detection
"""

import base64
import json
import io
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

try:
    import pytesseract
    import cv2
    import numpy as np
    from PIL import Image
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

from dmitry_operator.vision import VisionSystem, ScreenCapture


@dataclass
class TextRegion:
    text: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x, y, width, height


@dataclass
class UIElement:
    type: str  # button, input, text, icon
    text: Optional[str]
    bbox: Tuple[int, int, int, int]
    confidence: float
    clickable: bool = False


class EnhancedVision(VisionSystem):
    def __init__(self, cache_dir: str = None):
        super().__init__(cache_dir)
        if not HAS_OCR:
            print("Warning: OCR dependencies missing. Run: pip install pytesseract opencv-python")
    
    def extract_text_from_capture(self, capture: ScreenCapture) -> List[TextRegion]:
        """Extract text using OCR"""
        if not HAS_OCR:
            return []
        
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(capture.image_data))
            
            # Use pytesseract to get detailed text info
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            regions = []
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                if text and int(data['conf'][i]) > 30:  # Confidence threshold
                    regions.append(TextRegion(
                        text=text,
                        confidence=int(data['conf'][i]) / 100.0,
                        bbox=(data['left'][i], data['top'][i], data['width'][i], data['height'][i])
                    ))
            
            return regions
        except Exception as e:
            print(f"OCR failed: {e}")
            return []
    
    def detect_ui_elements(self, capture: ScreenCapture) -> List[UIElement]:
        """Detect UI elements using computer vision"""
        if not HAS_OCR:
            return []
        
        try:
            # Convert to OpenCV format
            image = Image.open(io.BytesIO(capture.image_data))
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            elements = []
            
            # Detect buttons (rectangles with text)
            contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter by size (likely UI elements)
                if 20 < w < 300 and 15 < h < 100:
                    # Extract text from this region
                    roi = gray[y:y+h, x:x+w]
                    text = pytesseract.image_to_string(roi).strip()
                    
                    if text:
                        elements.append(UIElement(
                            type="button" if w > h else "text",
                            text=text,
                            bbox=(x, y, w, h),
                            confidence=0.7,
                            clickable=True if w > h else False
                        ))
            
            return elements[:20]  # Limit results
        except Exception as e:
            print(f"UI detection failed: {e}")
            return []
    
    def find_clickable_element(self, description: str) -> Optional[Tuple[int, int]]:
        """Find element by description and return click coordinates"""
        capture = self.capture_screen()
        if not capture:
            return None
        
        # Get text regions and UI elements
        text_regions = self.extract_text_from_capture(capture)
        ui_elements = self.detect_ui_elements(capture)
        
        description_lower = description.lower()
        
        # Search in text regions first
        for region in text_regions:
            if description_lower in region.text.lower():
                x = region.bbox[0] + region.bbox[2] // 2
                y = region.bbox[1] + region.bbox[3] // 2
                return (x, y)
        
        # Search in UI elements
        for element in ui_elements:
            if element.text and description_lower in element.text.lower():
                x = element.bbox[0] + element.bbox[2] // 2
                y = element.bbox[1] + element.bbox[3] // 2
                return (x, y)
        
        return None
    
    def get_screen_text_summary(self) -> str:
        """Get a summary of all visible text"""
        capture = self.capture_screen()
        if not capture:
            return "Could not capture screen"
        
        text_regions = self.extract_text_from_capture(capture)
        
        if not text_regions:
            return "No text detected on screen"
        
        # Group by confidence and relevance
        important_text = [r.text for r in text_regions if r.confidence > 0.7 and len(r.text) > 2]
        
        return " | ".join(important_text[:10])  # Top 10 text elements
    
    def smart_click(self, description: str) -> Dict[str, Any]:
        """Smart click that finds and clicks elements by description"""
        coords = self.find_clickable_element(description)
        
        if coords:
            try:
                import pyautogui
                pyautogui.click(coords[0], coords[1])
                return {
                    "success": True,
                    "message": f"Clicked at {coords}",
                    "coordinates": coords
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        else:
            return {"success": False, "error": f"Could not find '{description}' on screen"}


# Global instance
enhanced_vision = EnhancedVision()