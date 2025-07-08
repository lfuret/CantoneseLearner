import io
import re
from typing import Optional

class FileParser:
    """Handles parsing of different file formats to extract text content."""
    
    def __init__(self):
        self.supported_types = {
            'application/pdf': self._parse_pdf,
            'application/epub+zip': self._parse_epub,
            'text/plain': self._parse_txt,
            'application/octet-stream': self._parse_by_extension  # Fallback for some uploads
        }
    
    def parse_file(self, file_path: str, mime_type: str) -> str:
        """
        Parse a file and extract text content.
        
        Args:
            file_path: Path to the file to parse
            mime_type: MIME type of the file
            
        Returns:
            Extracted text content as string
            
        Raises:
            ValueError: If file type is not supported
            Exception: If parsing fails
        """
        if mime_type in self.supported_types:
            return self.supported_types[mime_type](file_path)
        else:
            # Try to determine by file extension
            return self._parse_by_extension(file_path)
    
    def _parse_pdf(self, file_path: str) -> str:
        """Parse PDF file and extract text content."""
        try:
            import PyPDF2
            
            text_content = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text_content += page.extract_text() + "\n"
            
            return text_content
            
        except ImportError:
            # Fallback to pdfplumber if PyPDF2 is not available
            try:
                import pdfplumber
                
                text_content = ""
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_content += page_text + "\n"
                
                return text_content
                
            except ImportError:
                raise Exception("PDF parsing libraries not available. Please install PyPDF2 or pdfplumber.")
        
        except Exception as e:
            raise Exception(f"Failed to parse PDF: {str(e)}")
    
    def _parse_epub(self, file_path: str) -> str:
        """Parse EPUB file and extract text content."""
        try:
            import ebooklib
            from ebooklib import epub
            import html2text
            
            book = epub.read_epub(file_path)
            text_content = ""
            
            # Convert HTML to text
            h = html2text.HTML2Text()
            h.ignore_links = True
            h.ignore_images = True
            
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    content = item.get_content().decode('utf-8')
                    text_content += h.handle(content) + "\n"
            
            return text_content
            
        except ImportError:
            raise Exception("EPUB parsing library not available. Please install ebooklib and html2text.")
        
        except Exception as e:
            raise Exception(f"Failed to parse EPUB: {str(e)}")
    
    def _parse_txt(self, file_path: str) -> str:
        """Parse text file and return content."""
        try:
            # Try different encodings
            encodings = ['utf-8', 'utf-16', 'gb2312', 'gbk', 'big5']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        return file.read()
                except UnicodeDecodeError:
                    continue
            
            # If all encodings fail, try with error handling
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                return file.read()
                
        except Exception as e:
            raise Exception(f"Failed to parse text file: {str(e)}")
    
    def _parse_by_extension(self, file_path: str) -> str:
        """Determine parsing method by file extension."""
        file_path_lower = file_path.lower()
        
        if file_path_lower.endswith('.pdf'):
            return self._parse_pdf(file_path)
        elif file_path_lower.endswith('.epub'):
            return self._parse_epub(file_path)
        elif file_path_lower.endswith(('.txt', '.text')):
            return self._parse_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type. Supported formats: PDF, EPUB, TXT")
    
    def is_supported_file(self, filename: str) -> bool:
        """Check if a file type is supported based on filename."""
        supported_extensions = ['.pdf', '.epub', '.txt', '.text']
        return any(filename.lower().endswith(ext) for ext in supported_extensions)
