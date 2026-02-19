# ui.py - Dmitry v1.2
"""
Dmitry UI - Main interface with mode indicator and tool transparency.
"""

import os
import time
import random
import tkinter as tk
from collections import deque
from typing import Callable, Optional
from PIL import Image, ImageTk, ImageDraw, ImageFilter
from tkinter.scrolledtext import ScrolledText


class DmitryUI:
    """
    Dmitry's visual interface.
    
    Features:
    - Animated face with speaking visualization
    - Mode indicator
    - Chat log with typing animation
    - Tool execution display
    - Confirmation dialogs
    """
    
    def __init__(self, face_path: str, size: tuple = (760, 760)):
        """
        Initialize the UI.
        
        Args:
            face_path: Path to the face image
            size: Window size (width, height)
        """
        self.root = tk.Tk()
        self.root.title("D.M.I.T.R.Y")
        self.root.resizable(False, False)
        
        # Window dimensions
        self.width = 760
        self.height = 900
        self.root.geometry(f"{self.width}x{self.height}")
        self.root.configure(bg="#000000")

        # Face dimensions
        full_size = (self.width, self.height)
        self.size = full_size 
        
        # Canvas for face animation
        self.canvas = tk.Canvas(
            self.root,
            width=self.width,
            height=self.height,
            bg="#000000",
            highlightthickness=0
        )
        self.canvas.place(relx=0.5, rely=0.5, anchor="center")

        # Load face image
        self.face_base = (
            Image.open(face_path)
            .convert("RGBA")
            .resize(full_size, Image.LANCZOS)
        )

        # Create halo effect
        self.halo_base = self._create_halo(full_size, radius=300, y_offset=0)

        # Animation state
        self.speaking = False
        self.scale = 1.0
        self.target_scale = 1.0
        self.halo_alpha = 70
        self.target_halo_alpha = 70
        self.last_target_time = time.time()

        # Mode indicator
        self._current_mode = "general"
        self._mode_icon = "🧠"
        self.mode_label = tk.Label(
            self.root,
            text="🧠 GENERAL MODE",
            fg="#8ffcff",
            bg="#000000",
            font=("Consolas", 11, "bold"),
        )
        self.mode_label.place(relx=0.02, rely=0.02)

        # Chat log
        self.text_box = ScrolledText(
            self.root,
            fg="#8ffcff",
            bg="#000000",
            insertbackground="#8ffcff",
            height=12,
            width=68,
            borderwidth=0,
            wrap="word",
            font=("Consolas", 10),
            padx=12,
            pady=12
        )
        self.text_box.place(relx=0.5, rely=0.86, anchor="center")
        self.text_box.configure(state="disabled")
        
        # Configure text tags for different message types
        self.text_box.tag_configure("user", foreground="#ffffff")
        self.text_box.tag_configure("ai", foreground="#8ffcff")
        self.text_box.tag_configure("system", foreground="#ffcc00")
        self.text_box.tag_configure("tool", foreground="#00ff88")
        self.text_box.tag_configure("error", foreground="#ff6666")

        # Typing animation state
        self.typing_queue = deque()
        self.is_typing = False

        # Confirmation dialog callback
        self._confirm_callback: Optional[Callable[[str], bool]] = None

        # Start animation loop
        self._animate()
        self.root.protocol("WM_DELETE_WINDOW", lambda: os._exit(0))

    def _create_halo(self, size: tuple, radius: int, y_offset: int) -> Image.Image:
        """Create the glowing halo effect."""
        w, h = size
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        cx = w // 2
        cy = h // 2 + y_offset

        for r in range(radius, 0, -12):
            alpha = int(70 * (1 - r / radius))
            draw.ellipse(
                (cx - r, cy - r, cx + r, cy + r),
                fill=(0, 180, 255, alpha)
            )

        return img.filter(ImageFilter.GaussianBlur(30))

    def set_mode(self, mode_name: str, icon: str = "🧠") -> None:
        """
        Update the mode indicator.
        
        Args:
            mode_name: Name of the current mode
            icon: Mode icon emoji
        """
        self._current_mode = mode_name
        self._mode_icon = icon
        self.mode_label.configure(text=f"{icon} {mode_name.upper()} MODE")
        
        # Flash the mode indicator
        self.mode_label.configure(fg="#ffffff")
        self.root.after(200, lambda: self.mode_label.configure(fg="#8ffcff"))

    def _clean_log(self) -> None:
        """Keep only the last 5 conversation pairs."""
        try:
            content = self.text_box.get("1.0", tk.END)
            if content.count("You:") > 5:
                first_pos = self.text_box.search("You:", "1.0", stopindex=tk.END)
                if first_pos:
                    next_start = f"{first_pos} + 1 chars"
                    second_pos = self.text_box.search("You:", next_start, stopindex=tk.END)
                    if second_pos:
                        self.text_box.delete("1.0", second_pos)
        except Exception:
            pass

    def write_log(self, text: str, tag: str = None) -> None:
        """
        Add text to the chat log with typing animation.
        
        Args:
            text: Text to display
            tag: Optional tag for styling ("user", "ai", "system", "tool", "error")
        """
        self.text_box.configure(state="normal")
        self._clean_log()
        self.text_box.configure(state="disabled")

        self.typing_queue.append((text, tag))
        if not self.is_typing:
            self._start_typing()

    def _start_typing(self) -> None:
        """Start typing animation for queued text."""
        if not self.typing_queue:
            self.is_typing = False
            return

        self.is_typing = True
        text, tag = self.typing_queue.popleft()

        self.text_box.configure(state="normal")
        self._type_char(text, 0, tag)

    def _type_char(self, text: str, i: int, tag: str = None) -> None:
        """Type one character at a time."""
        if i < len(text):
            if tag:
                self.text_box.insert(tk.END, text[i], tag)
            else:
                self.text_box.insert(tk.END, text[i])
            self.text_box.see(tk.END)
            self.root.after(12, self._type_char, text, i + 1, tag)
        else:
            self.text_box.insert(tk.END, "\n")
            self.text_box.configure(state="disabled")
            self.root.after(40, self._start_typing)

    def write_immediate(self, text: str, tag: str = None) -> None:
        """Write text immediately without animation."""
        self.text_box.configure(state="normal")
        if tag:
            self.text_box.insert(tk.END, text + "\n", tag)
        else:
            self.text_box.insert(tk.END, text + "\n")
        self.text_box.see(tk.END)
        self.text_box.configure(state="disabled")

    def show_tool_execution(self, tool_name: str, status: str = "running") -> None:
        """
        Show tool execution in the log.
        
        Args:
            tool_name: Name of the tool
            status: "running", "success", or "failed"
        """
        if status == "running":
            self.write_immediate(f"⚙️ Executing: {tool_name}...", "tool")
        elif status == "success":
            self.write_immediate(f"✓ {tool_name} completed", "tool")
        else:
            self.write_immediate(f"✗ {tool_name} failed", "error")

    def start_speaking(self) -> None:
        """Start speaking animation."""
        self.speaking = True

    def stop_speaking(self) -> None:
        """Stop speaking animation."""
        self.speaking = False

    def confirm_action(self, message: str) -> bool:
        """
        Show a confirmation dialog.
        
        Args:
            message: Confirmation message to display
            
        Returns:
            True if confirmed, False otherwise
        """
        from tkinter import messagebox
        return messagebox.askyesno("Confirm Action", message)

    def set_confirm_callback(self, callback: Callable[[str], bool]) -> None:
        """Set external confirmation callback."""
        self._confirm_callback = callback

    def get_confirm_callback(self) -> Callable[[str], bool]:
        """Get the confirmation callback."""
        return self._confirm_callback or self.confirm_action

    def _animate(self) -> None:
        """Main animation loop."""
        now = time.time()

        # Update target values periodically
        if now - self.last_target_time > (0.15 if self.speaking else 0.7):
            if self.speaking:
                self.target_scale = random.uniform(1.12, 1.18)
                self.target_halo_alpha = random.randint(140, 180)
            else:
                self.target_scale = random.uniform(1.004, 1.012)
                self.target_halo_alpha = random.randint(60, 80)

            self.last_target_time = now

        # Smooth interpolation
        scale_speed = 0.55 if self.speaking else 0.25
        halo_speed = 0.50 if self.speaking else 0.25

        self.scale += (self.target_scale - self.scale) * scale_speed
        self.halo_alpha += (self.target_halo_alpha - self.halo_alpha) * halo_speed

        # Compose frame
        frame = Image.new("RGBA", self.size, (0, 0, 0, 255))

        # Add halo
        halo = self.halo_base.copy()
        halo.putalpha(int(self.halo_alpha))
        frame.alpha_composite(halo)

        # Add scaled face
        w, h = self.size
        face = self.face_base.resize(
            (int(w * self.scale), int(h * self.scale)),
            Image.LANCZOS
        )

        fx = (w - face.size[0]) // 2
        fy = (h - face.size[1]) // 2
        frame.alpha_composite(face, (fx, fy))

        # Update canvas
        img = ImageTk.PhotoImage(frame)
        self.canvas.delete("all")
        self.canvas.create_image(w // 2, h // 2, image=img)
        self.canvas.image = img

        # Schedule next frame
        self.root.after(16, self._animate)


# Backward compatibility alias
JarvisUI = DmitryUI
