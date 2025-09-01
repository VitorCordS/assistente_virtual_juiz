import PyPDF2
import pdfplumber
import logging
from io import BytesIO
import re

class PDFProcessor:
    """Serviço para extrair texto de arquivos PDF"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract_text_from_pdf(self, pdf_path_or_bytes):
        """Extrai texto de um arquivo PDF usando múltiplas estratégias"""
        try:
            # Tenta primeiro com pdfplumber (melhor para layout complexo)
            text = self._extract_with_pdfplumber(pdf_path_or_bytes)
            
            if not text or len(text.strip()) < 100:
                # Se não conseguiu texto suficiente, tenta com PyPDF2
                text = self._extract_with_pypdf2(pdf_path_or_bytes)
            
            # Limpa e normaliza o texto extraído
            cleaned_text = self._clean_extracted_text(text)
            
            return cleaned_text
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair texto do PDF: {e}")
            return ""
    
    def _extract_with_pdfplumber(self, pdf_path_or_bytes):
        """Extrai texto usando pdfplumber"""
        text = ""
        
        try:
            if isinstance(pdf_path_or_bytes, (str, bytes)):
                # Se for caminho do arquivo ou bytes
                with pdfplumber.open(pdf_path_or_bytes) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            
        except Exception as e:
            self.logger.warning(f"Erro com pdfplumber: {e}")
        
        return text
    
    def _extract_with_pypdf2(self, pdf_path_or_bytes):
        """Extrai texto usando PyPDF2"""
        text = ""
        
        try:
            if isinstance(pdf_path_or_bytes, str):
                # Se for caminho do arquivo
                with open(pdf_path_or_bytes, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            
            elif isinstance(pdf_path_or_bytes, bytes):
                # Se for bytes
                pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_path_or_bytes))
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
        except Exception as e:
            self.logger.warning(f"Erro com PyPDF2: {e}")
        
        return text
    
    def _clean_extracted_text(self, text):
        """Limpa e normaliza o texto extraído"""
        if not text:
            return ""
        
        # Remove caracteres de controle e normaliza espaços
        text = re.sub(r'\s+', ' ', text)
        
        # Remove quebras de linha desnecessárias
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remove caracteres especiais problemáticos
        text = re.sub(r'[^\w\s\.,;:!?\-\(\)\[\]\"\'\/\n\r]', '', text)
        
        # Normaliza pontuação
        text = re.sub(r'\s+([,.;:!?])', r'\1', text)
        
        return text.strip()
    
    def extract_metadata(self, pdf_path_or_bytes):
        """Extrai metadados do PDF"""
        metadata = {}
        
        try:
            if isinstance(pdf_path_or_bytes, str):
                with open(pdf_path_or_bytes, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    if pdf_reader.metadata:
                        metadata = {
                            'title': pdf_reader.metadata.get('/Title', ''),
                            'author': pdf_reader.metadata.get('/Author', ''),
                            'subject': pdf_reader.metadata.get('/Subject', ''),
                            'creator': pdf_reader.metadata.get('/Creator', ''),
                            'producer': pdf_reader.metadata.get('/Producer', ''),
                            'creation_date': pdf_reader.metadata.get('/CreationDate', ''),
                            'modification_date': pdf_reader.metadata.get('/ModDate', '')
                        }
                    metadata['num_pages'] = len(pdf_reader.pages)
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair metadados: {e}")
        
        return metadata
    
    def validate_pdf(self, pdf_path_or_bytes):
        """Valida se o arquivo é um PDF válido"""
        try:
            if isinstance(pdf_path_or_bytes, str):
                with open(pdf_path_or_bytes, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    return len(pdf_reader.pages) > 0
            
            elif isinstance(pdf_path_or_bytes, bytes):
                pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_path_or_bytes))
                return len(pdf_reader.pages) > 0
            
        except Exception as e:
            self.logger.error(f"PDF inválido: {e}")
            return False
        
        return False

