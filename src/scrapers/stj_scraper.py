from .base_scraper import BaseScraper
from datetime import datetime, timedelta
import re

class STJScraper(BaseScraper):
    """Scraper para jurisprudência do Superior Tribunal de Justiça (STJ)"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.stj.jus.br"
        self.search_url = f"{self.base_url}/sites/portalp/Paginas/Jurisprudencia/Pesquisa-de-Jurisprudencia.aspx"
    
    def get_tribunal_name(self):
        return "STJ"
    
    def search_recent_decisions(self, days_back=7):
        """Busca decisões recentes do STJ"""
        decisions = []
        
        try:
            # Data de início da busca
            start_date = datetime.now() - timedelta(days=days_back)
            
            # O STJ pode ter uma estrutura diferente de busca
            # Aqui implementaríamos a lógica específica para o STJ
            
            response = self.get_page(self.search_url)
            if not response:
                return decisions
            
            soup = self.parse_html(response.text)
            
            # Busca pelos resultados (estrutura específica do STJ)
            result_items = soup.find_all('div', class_='resultado') or soup.find_all('tr', class_='linha-resultado')
            
            for item in result_items:
                decision_data = self._extract_basic_info(item)
                if decision_data:
                    decisions.append(decision_data)
            
        except Exception as e:
            self.logger.error(f"Erro na busca de decisões do STJ: {e}")
        
        return decisions
    
    def _extract_basic_info(self, item_element):
        """Extrai informações básicas de um item de resultado"""
        try:
            # Busca pelo link da decisão
            link_element = item_element.find('a', href=True)
            if not link_element:
                return None
            
            url = link_element.get('href')
            if not url.startswith('http'):
                url = f"{self.base_url}{url}"
            
            # Extrai número do processo
            numero_processo = self._extract_process_number(item_element.get_text())
            
            # Extrai relator
            relator = self._extract_relator(item_element.get_text())
            
            return {
                'url': url,
                'numero_processo': numero_processo,
                'relator': relator,
                'tribunal': self.get_tribunal_name()
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair informações básicas: {e}")
            return None
    
    def _extract_process_number(self, text):
        """Extrai número do processo do texto"""
        # Padrão para números de processo do STJ
        pattern = r'(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})'
        match = re.search(pattern, text)
        return match.group(1) if match else ""
    
    def _extract_relator(self, text):
        """Extrai nome do relator do texto"""
        # Busca por padrões como "Rel.: Nome do Ministro"
        pattern = r'Rel\.?:?\s*([A-ZÁÊÇÕ\s]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else ""
    
    def extract_decision_details(self, decision_url):
        """Extrai detalhes completos de uma decisão específica"""
        try:
            response = self.get_page(decision_url)
            if not response:
                return None
            
            soup = self.parse_html(response.text)
            
            # Extrai informações detalhadas
            details = {
                'tribunal': self.get_tribunal_name(),
                'url_origem': decision_url,
                'numero_processo': self._extract_detailed_process_number(soup),
                'relator': self._extract_detailed_relator(soup),
                'data_julgamento': self._extract_judgment_date(soup),
                'data_publicacao': self._extract_publication_date(soup),
                'ementa': self._extract_ementa(soup),
                'acordao': self._extract_acordao(soup),
                'tags': self._extract_tags(soup)
            }
            
            return details
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair detalhes da decisão {decision_url}: {e}")
            return None
    
    def _extract_detailed_process_number(self, soup):
        """Extrai número do processo da página de detalhes"""
        process_element = soup.find('span', class_='processo') or soup.find('div', class_='numero-processo')
        if process_element:
            return self.clean_text(process_element.get_text())
        return ""
    
    def _extract_detailed_relator(self, soup):
        """Extrai relator da página de detalhes"""
        relator_element = soup.find('span', class_='relator') or soup.find('div', class_='relator')
        if relator_element:
            return self.clean_text(relator_element.get_text())
        return ""
    
    def _extract_judgment_date(self, soup):
        """Extrai data de julgamento"""
        date_element = soup.find('span', class_='data-julgamento') or soup.find('div', class_='data-julgamento')
        if date_element:
            return self.extract_date(self.clean_text(date_element.get_text()))
        return None
    
    def _extract_publication_date(self, soup):
        """Extrai data de publicação"""
        date_element = soup.find('span', class_='data-publicacao') or soup.find('div', class_='data-publicacao')
        if date_element:
            return self.extract_date(self.clean_text(date_element.get_text()))
        return None
    
    def _extract_ementa(self, soup):
        """Extrai ementa da decisão"""
        ementa_element = soup.find('div', class_='ementa') or soup.find('p', class_='ementa')
        if ementa_element:
            return self.clean_text(ementa_element.get_text())
        return ""
    
    def _extract_acordao(self, soup):
        """Extrai texto do acórdão"""
        acordao_element = soup.find('div', class_='acordao') or soup.find('div', class_='inteiro-teor')
        if acordao_element:
            return self.clean_text(acordao_element.get_text())
        return ""
    
    def _extract_tags(self, soup):
        """Extrai palavras-chave/tags"""
        tags_elements = soup.find_all('span', class_='tag') or soup.find_all('div', class_='palavra-chave')
        tags = [self.clean_text(tag.get_text()) for tag in tags_elements]
        return ', '.join(tags) if tags else ""

