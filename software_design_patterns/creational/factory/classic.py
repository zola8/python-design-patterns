from abc import ABC
from abc import abstractmethod


# 1. The Product Interface
class DocumentReader(ABC):
    @abstractmethod
    def extract_text(self) -> str: pass


class PDFReader(DocumentReader):
    def extract_text(self) -> str: return "Extracted PDF text..."


class DocxReader(DocumentReader):
    def extract_text(self) -> str: return "Extracted DOCX text..."


# 2. The Creator (Base Class)
class Document(ABC):
    def __init__(self, file_path: str):
        self.file_path = file_path
        # The Factory Method is called here!
        self.reader = self._create_reader()

    @abstractmethod
    def _create_reader(self) -> DocumentReader:
        pass  # Subclasses must implement this

    def process(self):
        # Base class uses the created object without knowing its concrete type
        text = self.reader.extract_text()
        print(f"Processing {self.file_path}: {text}")


# 3. The Concrete Creators (Subclasses)
class PDFDocument(Document):
    def _create_reader(self) -> DocumentReader:
        return PDFReader()


class DocxDocument(Document):
    def _create_reader(self) -> DocumentReader:
        return DocxReader()


if __name__ == '__main__':
    doc = PDFDocument("report.pdf")
    doc.process()
