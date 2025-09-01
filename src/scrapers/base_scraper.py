import requests
import time
import random
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging

class BaseScraper(ABC):
    """Classe base para todos os scrapers de jurisprudência"""
    
    def __init__(self, delay_range=(1, 3)):
        self.session = requests.Session()
        self.delay_range = delay_range
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Headers para simular um navegador real
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def get_page(self, url, params=None, timeout=30):
        """Faz uma requisição HTTP com delay aleatório para evitar sobrecarga"""
        try:
            # Delay aleatório entre requisições
            delay = random.uniform(*self.delay_range)
            time.sleep(delay)
            
            response = self.session.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            self.logger.error(f"Erro ao acessar {url}: {e}")
            return None
    
    def parse_html(self, html_content):
        """Converte HTML em objeto BeautifulSoup"""
        return BeautifulSoup(html_content, 'html.parser')
    
    def clean_text(self, text):
        """Limpa e normaliza texto extraído"""
        if not text:
            return ""
        
        # Remove espaços extras e quebras de linha desnecessárias
        text = ' '.join(text.split())
        return text.strip()
    
    def extract_date(self, date_string):
        """Extrai e converte datas para formato padrão"""
        # Implementar parsing de datas específico para cada tribunal
        # Por enquanto, retorna a string original
        return date_string
    
    @abstractmethod
    def get_tribunal_name(self):
        """Retorna o nome do tribunal (STF, STJ, etc.)"""
        pass
    
    @abstractmethod
    def search_recent_decisions(self, days_back=7):
        """Busca decisões recentes dos últimos N dias"""
        pass
    
    @abstractmethod
    def extract_decision_details(self, decision_url):
        """Extrai detalhes completos de uma decisão específica"""
        pass
    
    def get_recent_jurisprudence(self, days_back=7):
        """Método principal para coletar jurisprudência recente"""
        self.logger.info(f"Iniciando coleta de jurisprudência do {self.get_tribunal_name()}")
        
        try:
            # Busca decisões recentes
            decisions = self.search_recent_decisions(days_back)
            
            # Extrai detalhes de cada decisão
            detailed_decisions = []
            for decision in decisions:
                details = self.extract_decision_details(decision.get('url'))
                if details:
                    detailed_decisions.append(details)
            
            self.logger.info(f"Coletadas {len(detailed_decisions)} decisões do {self.get_tribunal_name()}")
            return detailed_decisions
            
        except Exception as e:
            self.logger.error(f"Erro na coleta do {self.get_tribunal_name()}: {e}")
            return []

