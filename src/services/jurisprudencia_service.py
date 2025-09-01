from src.models.jurisprudencia import db, Jurisprudencia, Enunciado
from src.scrapers.stf_scraper import STFScraper
from src.scrapers.stj_scraper import STJScraper
from src.scrapers.tjsp_scraper import TJSPScraper
from src.scrapers.enunciados_scraper import EnunciadosScraper
import logging
from datetime import datetime

class JurisprudenciaService:
    """Serviço para gerenciar a coleta e armazenamento de jurisprudência"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scrapers = {
            'STF': STFScraper(),
            'STJ': STJScraper(),
            'TJSP': TJSPScraper(),
            'ENUNCIADOS': EnunciadosScraper()
        }
    
    def collect_all_recent_jurisprudence(self, days_back=7):
        """Coleta jurisprudência recente de todos os tribunais"""
        self.logger.info(f"Iniciando coleta de jurisprudência dos últimos {days_back} dias")
        
        results = {
            'success': [],
            'errors': [],
            'total_collected': 0
        }
        
        # Coleta de cada tribunal
        for tribunal_name, scraper in self.scrapers.items():
            try:
                if tribunal_name == 'ENUNCIADOS':
                    # Para enunciados, coletamos todos, não apenas recentes
                    enunciados = scraper.get_all_enunciados()
                    saved_count = self._save_enunciados(enunciados)
                    results['success'].append(f"{tribunal_name}: {saved_count} enunciados coletados")
                    results['total_collected'] += saved_count
                else:
                    # Para tribunais, coletamos jurisprudência recente
                    decisions = scraper.get_recent_jurisprudence(days_back)
                    saved_count = self._save_jurisprudencia(decisions)
                    results['success'].append(f"{tribunal_name}: {saved_count} decisões coletadas")
                    results['total_collected'] += saved_count
                    
            except Exception as e:
                error_msg = f"Erro na coleta do {tribunal_name}: {str(e)}"
                self.logger.error(error_msg)
                results['errors'].append(error_msg)
        
        self.logger.info(f"Coleta finalizada. Total: {results['total_collected']} itens")
        return results
    
    def _save_jurisprudencia(self, decisions):
        """Salva decisões de jurisprudência no banco de dados"""
        saved_count = 0
        
        for decision in decisions:
            try:
                # Verifica se já existe no banco
                existing = Jurisprudencia.query.filter_by(
                    tribunal=decision.get('tribunal'),
                    numero_processo=decision.get('numero_processo')
                ).first()
                
                if existing:
                    continue  # Pula se já existe
                
                # Cria nova entrada
                jurisprudencia = Jurisprudencia(
                    tribunal=decision.get('tribunal'),
                    numero_processo=decision.get('numero_processo'),
                    relator=decision.get('relator'),
                    data_julgamento=self._parse_date(decision.get('data_julgamento')),
                    data_publicacao=self._parse_date(decision.get('data_publicacao')),
                    ementa=decision.get('ementa'),
                    acordao=decision.get('acordao'),
                    tags=decision.get('tags'),
                    url_origem=decision.get('url_origem')
                )
                
                db.session.add(jurisprudencia)
                saved_count += 1
                
            except Exception as e:
                self.logger.error(f"Erro ao salvar decisão: {e}")
                continue
        
        try:
            db.session.commit()
            self.logger.info(f"Salvadas {saved_count} decisões no banco de dados")
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Erro ao fazer commit: {e}")
            saved_count = 0
        
        return saved_count
    
    def _save_enunciados(self, enunciados):
        """Salva enunciados no banco de dados"""
        saved_count = 0
        
        for enunciado_data in enunciados:
            try:
                # Verifica se já existe no banco
                existing = Enunciado.query.filter_by(
                    orgao=enunciado_data.get('orgao'),
                    tipo=enunciado_data.get('tipo'),
                    numero=enunciado_data.get('numero')
                ).first()
                
                if existing:
                    continue  # Pula se já existe
                
                # Cria nova entrada
                enunciado = Enunciado(
                    orgao=enunciado_data.get('orgao'),
                    tipo=enunciado_data.get('tipo'),
                    numero=enunciado_data.get('numero'),
                    texto=enunciado_data.get('texto'),
                    observacoes=enunciado_data.get('observacoes'),
                    url_origem=enunciado_data.get('url_origem')
                )
                
                db.session.add(enunciado)
                saved_count += 1
                
            except Exception as e:
                self.logger.error(f"Erro ao salvar enunciado: {e}")
                continue
        
        try:
            db.session.commit()
            self.logger.info(f"Salvados {saved_count} enunciados no banco de dados")
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Erro ao fazer commit: {e}")
            saved_count = 0
        
        return saved_count
    
    def _parse_date(self, date_string):
        """Converte string de data para objeto datetime"""
        if not date_string:
            return None
        
        # Implementar parsing de datas específico
        # Por enquanto, retorna None
        return None
    
    def get_recent_jurisprudence(self, tribunal=None, limit=50):
        """Busca jurisprudência recente no banco de dados"""
        query = Jurisprudencia.query
        
        if tribunal:
            query = query.filter_by(tribunal=tribunal)
        
        jurisprudencia = query.order_by(Jurisprudencia.data_coleta.desc()).limit(limit).all()
        return [j.to_dict() for j in jurisprudencia]
    
    def get_enunciados(self, orgao=None, tipo=None, limit=100):
        """Busca enunciados no banco de dados"""
        query = Enunciado.query
        
        if orgao:
            query = query.filter_by(orgao=orgao)
        
        if tipo:
            query = query.filter_by(tipo=tipo)
        
        enunciados = query.order_by(Enunciado.numero).limit(limit).all()
        return [e.to_dict() for e in enunciados]
    
    def search_jurisprudence(self, search_term, tribunal=None, limit=50):
        """Busca jurisprudência por termo"""
        query = Jurisprudencia.query
        
        if tribunal:
            query = query.filter_by(tribunal=tribunal)
        
        # Busca no texto da ementa e acórdão
        query = query.filter(
            db.or_(
                Jurisprudencia.ementa.contains(search_term),
                Jurisprudencia.acordao.contains(search_term),
                Jurisprudencia.tags.contains(search_term)
            )
        )
        
        jurisprudencia = query.order_by(Jurisprudencia.data_coleta.desc()).limit(limit).all()
        return [j.to_dict() for j in jurisprudencia]

