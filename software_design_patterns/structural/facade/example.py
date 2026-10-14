# ==========================================
# 1. THE COMPLEX SUBSYSTEM (Many classes)
# ==========================================

class CloudStorage:
    def download(self, file_id: str) -> bytes:
        print(f"  [Storage] Downloading {file_id}...")
        return b"fake_video_data"

    def upload(self, data: bytes, destination: str):
        print(f"  [Storage] Uploading to {destination}...")


class AudioExtractor:
    def extract(self, video_data: bytes) -> bytes:
        print("  [Audio] Extracting audio track...")
        return b"fake_audio_data"


class VideoTranscoder:
    def convert(self, video_data: bytes, format: str) -> bytes:
        print(f"  [Transcoder] Converting to {format}...")
        return b"fake_mp4_data"


class ThumbnailGenerator:
    def generate(self, video_data: bytes, count: int) -> list[bytes]:
        print(f"  [Thumbnails] Generating {count} thumbnails...")
        return [b"thumb1", b"thumb2", b"thumb3"]


class Database:
    def update_video_status(self, video_id: str, status: str):
        print(f"  [DB] Updating video {video_id} to status: {status}")


# ==========================================
# 2. THE FACADE (Simple, unified interface)
# ==========================================

class VideoProcessingFacade:
    """
    Provides a simple interface for video processing.
    Orchestrates all the complex subsystems behind the scenes.
    """

    def __init__(self):
        self._storage = CloudStorage()
        self._audio_extractor = AudioExtractor()
        self._transcoder = VideoTranscoder()
        self._thumbnail_gen = ThumbnailGenerator()
        self._db = Database()

    def process_video(self, video_id: str, output_format: str = "mp4") -> dict:
        """
        The ONE method clients need to call.
        Handles the entire workflow end-to-end.
        """
        print(f"[Facade] Starting video processing for {video_id}")

        # Orchestrate the subsystem
        video_data = self._storage.download(video_id)

        audio = self._audio_extractor.extract(video_data)
        # (Maybe do something with audio, or just discard it)

        converted_video = self._transcoder.convert(video_data, output_format)

        thumbnails = self._thumbnail_gen.generate(video_data, count=5)

        self._storage.upload(converted_video, f"processed/{video_id}.{output_format}")
        for i, thumb in enumerate(thumbnails):
            self._storage.upload(thumb, f"thumbnails/{video_id}_thumb_{i}.jpg")

        self._db.update_video_status(video_id, "processed")

        print(f"[Facade] Video {video_id} processing complete!")
        return {
            "video_id": video_id,
            "format": output_format,
            "thumbnails_generated": len(thumbnails),
            "status": "success"
        }


# ==========================================
# 3. USAGE — Clean and Simple
# ==========================================

if __name__ == "__main__":
    facade = VideoProcessingFacade()

    result = facade.process_video("video_12345", output_format="mp4")
    print(f"\nResult: {result}")
