import random
import sys
import tkinter as tk
import os
from datetime import datetime


WIDTH, HEIGHT = 200, 200
PADDLE_WIDTH, PADDLE_HEIGHT = 6, 36
BALL_SIZE = 6

# Speeds are in pixels per frame
PLAYER_SPEED = 4
AI_MAX_SPEED = 2.8
INITIAL_BALL_SPEED_X_CHOICES = [-2, 2]
INITIAL_BALL_SPEED_Y_CHOICES = [-2, 2]


class PongGame:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Pong (200x200)")
        self.root.resizable(False, False)

        # Ensure client area is exactly 200x200
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="black", highlightthickness=0)
        self.canvas.pack()

        # Input state
        self.moving_up = False
        self.moving_down = False
        
        # Recording state
        self.recording = False
        self.recording_start_time = None
        self.frame_count = 0
        self.frames_dir = None

        # Create game objects
        self.player_x = 10
        self.ai_x = WIDTH - 10 - PADDLE_WIDTH
        self.player = self.canvas.create_rectangle(
            self.player_x,
            (HEIGHT - PADDLE_HEIGHT) // 2,
            self.player_x + PADDLE_WIDTH,
            (HEIGHT - PADDLE_HEIGHT) // 2 + PADDLE_HEIGHT,
            fill="white",
        )
        self.ai = self.canvas.create_rectangle(
            self.ai_x,
            (HEIGHT - PADDLE_HEIGHT) // 2,
            self.ai_x + PADDLE_WIDTH,
            (HEIGHT - PADDLE_HEIGHT) // 2 + PADDLE_HEIGHT,
            fill="white",
        )
        self.ball = self.canvas.create_rectangle(0, 0, BALL_SIZE, BALL_SIZE, fill="white")

        self.player_score = 0
        self.ai_score = 0
        self.score_text = self.canvas.create_text(
            WIDTH // 2,
            12,
            text=self._score_str(),
            fill="white",
            font=("Courier", 12),
        )

        # Bottom-row input indicators (overlay on top of gameplay)
        self.bottom_left = self.canvas.create_rectangle(
            0,
            HEIGHT - 2,
            WIDTH // 2,
            HEIGHT,
            fill="black",
            outline="",
        )
        self.bottom_right = self.canvas.create_rectangle(
            WIDTH // 2,
            HEIGHT - 2,
            WIDTH,
            HEIGHT,
            fill="black",
            outline="",
        )

        self.ball_dx = 0
        self.ball_dy = 0
        self.reset_ball(direction=random.choice([-1, 1]))

        # Bindings
        root.bind("<KeyPress-Up>", self._on_key_down)
        root.bind("<KeyRelease-Up>", self._on_key_up)
        root.bind("<KeyPress-Down>", self._on_key_down)
        root.bind("<KeyRelease-Down>", self._on_key_up)
        root.bind("<KeyPress-w>", self._on_key_down)
        root.bind("<KeyRelease-w>", self._on_key_up)
        root.bind("<KeyPress-s>", self._on_key_down)
        root.bind("<KeyRelease-s>", self._on_key_up)
        root.bind("<Escape>", lambda e: self._quit())
        root.bind("<KeyPress-r>", lambda e: self.reset_ball(direction=random.choice([-1, 1])))
        root.bind("<F1>", lambda e: self._toggle_recording())

        self.frame_delay_ms = 12  # ~83 FPS on paper; small window so it's fine
        self._tick()

    def _score_str(self) -> str:
        return f"{self.player_score} : {self.ai_score}"

    def _quit(self) -> None:
        try:
            self.root.destroy()
        except Exception:
            sys.exit(0)

    def _on_key_down(self, event: tk.Event) -> None:
        keysym = event.keysym.lower()
        if keysym in ("up", "w"):
            self.moving_up = True
        elif keysym in ("down", "s"):
            self.moving_down = True

    def _on_key_up(self, event: tk.Event) -> None:
        keysym = event.keysym.lower()
        if keysym in ("up", "w"):
            self.moving_up = False
        elif keysym in ("down", "s"):
            self.moving_down = False

    def reset_ball(self, direction: int = 1) -> None:
        # Center the ball
        bx = (WIDTH - BALL_SIZE) // 2
        by = (HEIGHT - BALL_SIZE) // 2
        self.canvas.coords(self.ball, bx, by, bx + BALL_SIZE, by + BALL_SIZE)
        self.ball_dx = random.choice(INITIAL_BALL_SPEED_X_CHOICES) * (1 if direction >= 0 else -1)
        self.ball_dy = random.choice(INITIAL_BALL_SPEED_Y_CHOICES)

    def _clamp_paddle(self, paddle_id: int) -> None:
        x1, y1, x2, y2 = self.canvas.coords(paddle_id)
        if y1 < 0:
            dy = -y1
            self.canvas.move(paddle_id, 0, dy)
        elif y2 > HEIGHT:
            dy = HEIGHT - y2
            self.canvas.move(paddle_id, 0, dy)

    def _move_player(self) -> None:
        dy = 0
        if self.moving_up:
            dy -= PLAYER_SPEED
        if self.moving_down:
            dy += PLAYER_SPEED
        if dy != 0:
            self.canvas.move(self.player, 0, dy)
            self._clamp_paddle(self.player)

    def _move_ai(self) -> None:
        # Simple tracking AI limited by AI_MAX_SPEED
        bx1, by1, bx2, by2 = self.canvas.coords(self.ball)
        ball_center_y = (by1 + by2) / 2
        ax1, ay1, ax2, ay2 = self.canvas.coords(self.ai)
        ai_center_y = (ay1 + ay2) / 2

        desired = ball_center_y
        delta = desired - ai_center_y
        # When ball is far from AI, nudge less to keep difficulty reasonable
        max_step = AI_MAX_SPEED
        if abs(delta) > max_step:
            step = max_step if delta > 0 else -max_step
        else:
            step = delta
        self.canvas.move(self.ai, 0, step)
        self._clamp_paddle(self.ai)

    def _ball_paddle_collision(self, paddle_id: int) -> bool:
        bx1, by1, bx2, by2 = self.canvas.coords(self.ball)
        px1, py1, px2, py2 = self.canvas.coords(paddle_id)
        return not (bx2 <= px1 or bx1 >= px2 or by2 <= py1 or by1 >= py2)

    def _reflect_from_paddle(self, paddle_id: int, is_left: bool) -> None:
        # Reverse horizontal, tweak vertical based on hit position
        self.ball_dx = -self.ball_dx

        bx1, by1, bx2, by2 = self.canvas.coords(self.ball)
        px1, py1, px2, py2 = self.canvas.coords(paddle_id)
        ball_center_y = (by1 + by2) / 2
        paddle_center_y = (py1 + py2) / 2
        offset = ball_center_y - paddle_center_y
        # Normalize offset to range [-1, 1] approximately
        normalized = max(-1.0, min(1.0, offset / (PADDLE_HEIGHT / 2)))
        # Bias dy by where it hit the paddle
        self.ball_dy += int(round(normalized * 4))
        self.ball_dy = max(-6, min(6, self.ball_dy))

        # Nudge ball outside paddle to avoid sticking
        if is_left:
            new_x1 = px2
            self.canvas.coords(self.ball, new_x1, by1, new_x1 + BALL_SIZE, by2)
        else:
            new_x2 = px1
            self.canvas.coords(self.ball, new_x2 - BALL_SIZE, by1, new_x2, by2)

    def _move_ball(self) -> None:
        # Move
        self.canvas.move(self.ball, self.ball_dx, self.ball_dy)
        bx1, by1, bx2, by2 = self.canvas.coords(self.ball)

        # Collide with top/bottom
        if by1 <= 0:
            self.ball_dy = abs(self.ball_dy)
            self.canvas.coords(self.ball, bx1, 0, bx2, BALL_SIZE)
        elif by2 >= HEIGHT:
            self.ball_dy = -abs(self.ball_dy)
            self.canvas.coords(self.ball, bx1, HEIGHT - BALL_SIZE, bx2, HEIGHT)

        # Collide with paddles
        if self.ball_dx < 0 and self._ball_paddle_collision(self.player):
            self._reflect_from_paddle(self.player, is_left=True)
        elif self.ball_dx > 0 and self._ball_paddle_collision(self.ai):
            self._reflect_from_paddle(self.ai, is_left=False)

        # Out of bounds (score)
        bx1, by1, bx2, by2 = self.canvas.coords(self.ball)
        if bx2 < 0:
            # AI scores
            self.ai_score += 1
            self.canvas.itemconfigure(self.score_text, text=self._score_str())
            self.reset_ball(direction=1)
        elif bx1 > WIDTH:
            # Player scores
            self.player_score += 1
            self.canvas.itemconfigure(self.score_text, text=self._score_str())
            self.reset_ball(direction=-1)

    def _tick(self) -> None:
        self._move_player()
        self._move_ai()
        self._move_ball()
        self._update_input_indicator()
        
        # Capture frame if recording (optimized to avoid blocking)
        if self.recording:
            self.root.after_idle(self._capture_frame)
        
        self.root.after(self.frame_delay_ms, self._tick)

    def _update_input_indicator(self) -> None:
        # Replace bottom row pixels to encode input state
        left_fill = "white" if self.moving_up else "black"
        right_fill = "white" if self.moving_down else "black"
        self.canvas.itemconfigure(self.bottom_left, fill=left_fill)
        self.canvas.itemconfigure(self.bottom_right, fill=right_fill)
        # Ensure indicators stay on top just in case
        self.canvas.tag_raise(self.bottom_left)
        self.canvas.tag_raise(self.bottom_right)

    def _toggle_recording(self) -> None:
        """Toggle frame recording on/off"""
        if not self.recording:
            # Start recording
            self.recording = True
            self.recording_start_time = datetime.now()
            self.frame_count = 0
            
            # Pre-calculate directory path once
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.frames_dir = os.path.join(script_dir, "frames")
            if not os.path.exists(self.frames_dir):
                os.makedirs(self.frames_dir)
            
            print(f"Recording started at {self.recording_start_time.strftime('%d/%m/%Y %H:%M:%S')}")
        else:
            # Stop recording
            self.recording = False
            print(f"Recording stopped. Captured {self.frame_count} frames.")

    def _capture_frame(self) -> None:
        """Capture current canvas as PNG file - optimized version"""
        try:
            # Pre-calculated timestamp to avoid repeated formatting
            if not hasattr(self, '_timestamp_str'):
                self._timestamp_str = self.recording_start_time.strftime("%d-%m-%Y_%H-%M-%S")
            
            filename = os.path.join(self.frames_dir, f"{self._timestamp_str}_{self.frame_count:04d}.png")
            
            # Remove canvas.update() call - it's unnecessary and slows things down
            # Canvas is already updated by the main game loop
            
            # Use more efficient screen capture
            x = self.canvas.winfo_rootx()
            y = self.canvas.winfo_rooty()
            
            # Import once at module level would be better, but doing it here to avoid import issues
            from PIL import ImageGrab
            
            # Capture without forcing window updates
            screenshot = ImageGrab.grab(bbox=(x, y, x + WIDTH, y + HEIGHT))
            screenshot.save(filename, "PNG", optimize=True)
            
            self.frame_count += 1
            
        except Exception as e:
            print(f"Error capturing frame: {e}")
            # Disable recording on error to prevent spam
            self.recording = False


def main() -> None:
    root = tk.Tk()
    PongGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
