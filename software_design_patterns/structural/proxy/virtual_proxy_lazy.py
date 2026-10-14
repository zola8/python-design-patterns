# Virtual Proxy (Lazy Loading)
import time
from abc import ABC
from abc import abstractmethod


# ==========================================
# 1. THE INTERFACE
# ==========================================
class Image(ABC):
    @abstractmethod
    def display(self) -> None: ...


# ==========================================
# 2. THE REAL OBJECT (Expensive to create)
# ==========================================
class RealImage(Image):
    def __init__(self, filename: str):
        self.filename = filename
        self._load_from_disk()  # Expensive operation!

    def _load_from_disk(self):
        print(f"  [RealImage] Loading '{self.filename}' from disk... (slow!)")
        # Simulate heavy work
        time.sleep(1)
        print(f"  [RealImage] Loaded successfully.")

    def display(self):
        print(f"  [RealImage] Displaying '{self.filename}'")


# ==========================================
# 3. THE PROXY (Lightweight placeholder)
# ==========================================
class ImageProxy(Image):
    def __init__(self, filename: str):
        self.filename = filename
        self._real_image: RealImage | None = None  # Not loaded yet!

    def display(self):
        # Only create the real object when display() is actually called
        if self._real_image is None:
            print("[Proxy] First display() call — loading real image now...")
            self._real_image = RealImage(self.filename)
        else:
            print("[Proxy] Image already loaded — reusing.")

        self._real_image.display()


if __name__ == '__main__':
    print("--- Creating images (instant, no disk I/O) ---")
    img1 = ImageProxy("vacation.jpg")
    img2 = ImageProxy("family.jpg")
    img3 = ImageProxy("work.png")

    print("\n--- Only displaying one of them ---")
    img1.display()  # NOW it loads

    print("\n--- Displaying it again (no reload) ---")
    img1.display()
