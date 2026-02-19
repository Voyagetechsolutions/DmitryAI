# tools/web/fetch_docs.py
"""
Fetch Docs Tool - Fetches and parses documentation pages.
"""

import re
import requests
from typing import Optional
from urllib.parse import urlparse
from html.parser import HTMLParser

from ..base_tool import BaseTool, ToolResult, ToolStatus
from ..permissions import PermissionLevel


class SimpleHTMLTextExtractor(HTMLParser):
    """Simple HTML to text converter."""
    
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self._skip_tags = {"script", "style", "noscript", "nav", "footer", "header"}
        self._current_skip = 0
        self._in_code = False
        self._code_buffer = []
    
    def handle_starttag(self, tag, attrs):
        if tag in self._skip_tags:
            self._current_skip += 1
        elif tag == "code" or tag == "pre":
            self._in_code = True
            self._code_buffer = []
        elif tag == "br":
            self.text_parts.append("\n")
        elif tag in ("p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li"):
            self.text_parts.append("\n")
    
    def handle_endtag(self, tag):
        if tag in self._skip_tags:
            self._current_skip = max(0, self._current_skip - 1)
        elif tag == "code" or tag == "pre":
            self._in_code = False
            if self._code_buffer:
                code = "".join(self._code_buffer)
                self.text_parts.append(f"\n```\n{code}\n```\n")
            self._code_buffer = []
        elif tag in ("p", "div", "h1", "h2", "h3", "h4", "h5", "h6"):
            self.text_parts.append("\n")
    
    def handle_data(self, data):
        if self._current_skip > 0:
            return
        
        text = data.strip()
        if text:
            if self._in_code:
                self._code_buffer.append(data)
            else:
                self.text_parts.append(text + " ")
    
    def get_text(self) -> str:
        text = "".join(self.text_parts)
        # Clean up extra whitespace
        text = re.sub(r"\n\s*\n", "\n\n", text)
        text = re.sub(r" +", " ", text)
        return text.strip()


class FetchDocsTool(BaseTool):
    """Tool to fetch and parse documentation pages."""
    
    # Maximum content length (100 KB)
    MAX_CONTENT_LENGTH = 100 * 1024
    
    # Request timeout
    TIMEOUT = 20
    
    def __init__(self):
        super().__init__()
        self._name = "fetch_docs"
        self._description = "Fetch and parse a documentation page"
        self._permission_level = PermissionLevel.READ
        self._needs_confirmation = False
    
    def get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL of the documentation page",
                },
                "extract_code": {
                    "type": "boolean",
                    "description": "Extract code blocks separately",
                    "default": True,
                },
                "max_length": {
                    "type": "integer",
                    "description": "Maximum text length to return",
                    "default": 5000,
                },
            },
            "required": ["url"],
        }
    
    def _validate_url(self, url: str) -> tuple[bool, str]:
        """Validate the URL."""
        try:
            parsed = urlparse(url)
            
            if parsed.scheme not in ("http", "https"):
                return False, "Only HTTP(S) URLs are supported"
            
            if not parsed.netloc:
                return False, "Invalid URL: missing domain"
            
            # Block localhost/internal URLs
            blocked_hosts = ["localhost", "127.0.0.1", "0.0.0.0", "::1"]
            if parsed.hostname in blocked_hosts:
                return False, "Cannot fetch from localhost"
            
            return True, "URL is valid"
            
        except Exception as e:
            return False, f"Invalid URL: {e}"
    
    def _extract_title(self, html: str) -> Optional[str]:
        """Extract page title from HTML."""
        match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None
    
    def _execute(
        self,
        url: str,
        extract_code: bool = True,
        max_length: int = 5000,
        **kwargs,
    ) -> ToolResult:
        """Fetch and parse the documentation page."""
        # Validate URL
        valid, msg = self._validate_url(url)
        if not valid:
            return ToolResult(
                status=ToolStatus.FAILED,
                error=msg,
            )
        
        try:
            # Fetch the page
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; DmitryBot/1.0; Documentation Fetcher)"
            }
            
            response = requests.get(
                url,
                headers=headers,
                timeout=self.TIMEOUT,
                stream=True,
            )
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type and "text/plain" not in content_type:
                return ToolResult(
                    status=ToolStatus.FAILED,
                    error=f"Unsupported content type: {content_type}",
                )
            
            # Read content with size limit
            content = ""
            for chunk in response.iter_content(chunk_size=8192, decode_unicode=True):
                if chunk:
                    content += chunk
                    if len(content) > self.MAX_CONTENT_LENGTH:
                        break
            
            # Parse HTML
            if "text/html" in content_type:
                parser = SimpleHTMLTextExtractor()
                parser.feed(content)
                text = parser.get_text()
                title = self._extract_title(content), 
            else:
                text = content
                title = None
            
            # Truncate if needed
            truncated = False
            if len(text) > max_length:
                text = text[:max_length] + "..."
                truncated = True
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                message=f"Fetched documentation from {urlparse(url).netloc}",
                data={
                    "url": url,
                    "title": title,
                    "content": text,
                    "length": len(text),
                    "truncated": truncated,
                    "source": urlparse(url).netloc,
                },
            )
            
        except requests.exceptions.Timeout:
            return ToolResult(
                status=ToolStatus.FAILED,
                error="Request timed out",
            )
        except requests.exceptions.HTTPError as e:
            return ToolResult(
                status=ToolStatus.FAILED,
                error=f"HTTP error: {e.response.status_code}",
            )
        except Exception as e:
            return ToolResult(
                status=ToolStatus.FAILED,
                error=f"Failed to fetch documentation: {e}",
            )
