from .base_scraper import BaseScraper
import re

class EnunciadosScraper(BaseScraper):
    """Scraper para enunciados do FONAJE e CNJ"""
    
    def __init__(self):
        super().__init__()
        self.fonaje_urls = {
            'civeis': 'https://www.cnj.jus.br/programas-e-acoes/juizados-especiais/enunciados-fonaje/enunciados-civeis/',
            'criminais': 'https://www.cnj.jus.br/programas-e-acoes/juizados-especiais/enunciados-fonaje/enunciados-criminais/',
            'fazenda_publica': 'https://www.cnj.jus.br/programas-e-acoes/juizados-especiais/enunciados-fonaje/enunciados-fazenda-publica/'
        }
        self.cnj_url = 'https://www.cnj.jus.br/enunciados/'
    
    def get_tribunal_name(self):
        return "ENUNCIADOS"
    
    def search_recent_decisions(self, days_back=7):
        """Para enunciados, coletamos todos, não apenas os recentes"""
        return self.get_all_enunciados()
    
    def get_all_enunciados(self):
        """Coleta todos os enunciados do FONAJE e CNJ"""
        all_enunciados = []
        
        # Coleta enunciados do FONAJE
        for tipo, url in self.fonaje_urls.items():
            enunciados = self._scrape_fonaje_enunciados(url, tipo)
            all_enunciados.extend(enunciados)
        
        # Coleta enunciados do CNJ
        enunciados_cnj = self._scrape_cnj_enunciados()
        all_enunciados.extend(enunciados_cnj)
        
        return all_enunciados
    
    def _scrape_fonaje_enunciados(self, url, tipo):
        """Coleta enunciados específicos do FONAJE"""
        enunciados = []
        
        try:
            response = self.get_page(url)
            if not response:
                return enunciados
            
            soup = self.parse_html(response.text)
            
            # Busca por enunciados na página
            # A estrutura pode variar, mas geralmente são parágrafos ou divs
            enunciado_elements = soup.find_all('p') or soup.find_all('div', class_='enunciado')
            
            for element in enunciado_elements:
                text = self.clean_text(element.get_text())
                
                # Verifica se é um enunciado (geralmente começa com "ENUNCIADO" seguido de número)
                if self._is_enunciado(text):
                    enunciado_data = self._parse_enunciado_text(text, 'FONAJE', tipo, url)
                    if enunciado_data:
                        enunciados.append(enunciado_data)
            
        except Exception as e:
            self.logger.error(f"Erro ao coletar enunciados FONAJE {tipo}: {e}")
        
        return enunciados
    
    def _scrape_cnj_enunciados(self):
        """Coleta enunciados do CNJ"""
        enunciados = []
        
        try:
            response = self.get_page(self.cnj_url)
            if not response:
                return enunciados
            
            soup = self.parse_html(response.text)
            
            # Busca por enunciados na página do CNJ
            enunciado_elements = soup.find_all('div', class_='enunciado') or soup.find_all('p')
            
            for element in enunciado_elements:
                text = self.clean_text(element.get_text())
                
                if self._is_enunciado(text):
                    enunciado_data = self._parse_enunciado_text(text, 'CNJ', 'GERAL', self.cnj_url)
                    if enunciado_data:
                        enunciados.append(enunciado_data)
            
        except Exception as e:
            self.logger.error(f"Erro ao coletar enunciados CNJ: {e}")
        
        return enunciados
    
    def _is_enunciado(self, text):
        """Verifica se o texto é um enunciado válido"""
        # Padrões comuns para identificar enunciados
        patterns = [
            r'ENUNCIADO\s+\d+',
            r'Enunciado\s+\d+',
            r'ENUNCIADO\s+N[ºº]\s*\d+'
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _parse_enunciado_text(self, text, orgao, tipo, url):
        """Extrai informações estruturadas do texto do enunciado"""
        try:
            # Extrai número do enunciado
            numero_match = re.search(r'ENUNCIADO\s+N?[ºº]?\s*(\d+)', text, re.IGNORECASE)
            numero = int(numero_match.group(1)) if numero_match else 0
            
            # Remove o cabeçalho "ENUNCIADO X" do texto
            texto_limpo = re.sub(r'ENUNCIADO\s+N?[ºº]?\s*\d+\s*[-–—]?\s*', '', text, flags=re.IGNORECASE)
            
            # Busca por observações (texto após "Obs:", "Observação:", etc.)
            obs_match = re.search(r'(Obs\.?|Observação|Nota):(.+)', texto_limpo, re.IGNORECASE | re.DOTALL)
            observacoes = obs_match.group(2).strip() if obs_match else ""
            
            # Remove observações do texto principal
            if obs_match:
                texto_limpo = texto_limpo[:obs_match.start()].strip()
            
            return {
                'orgao': orgao,
                'tipo': tipo.upper(),
                'numero': numero,
                'texto': texto_limpo.strip(),
                'observacoes': observacoes,
                'url_origem': url
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao processar enunciado: {e}")
            return None
    
    def extract_decision_details(self, decision_url):
        """Para enunciados, não há detalhes adicionais a extrair"""
        return None

