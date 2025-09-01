import os
import json
import logging
from datetime import datetime
from src.models.jurisprudencia import SentencaUsuario
from src.models.user import db
from src.services.pdf_processor import PDFProcessor
from src.services.style_analyzer import StyleAnalyzer

class SentenceService:
    """Serviço para gerenciar sentenças do usuário e aprendizado de estilo"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.pdf_processor = PDFProcessor()
        self.style_analyzer = StyleAnalyzer()
    
    def process_pdf_sentence(self, pdf_path, filename):
        """Processa um PDF de sentença e extrai características de estilo"""
        try:
            # Valida o PDF
            if not self.pdf_processor.validate_pdf(pdf_path):
                raise ValueError("Arquivo PDF inválido")
            
            # Extrai texto do PDF
            text = self.pdf_processor.extract_text_from_pdf(pdf_path)
            if not text or len(text.strip()) < 100:
                raise ValueError("Não foi possível extrair texto suficiente do PDF")
            
            # Analisa o estilo do texto
            style_analysis = self.style_analyzer.analyze_text_style(text)
            
            # Salva no banco de dados
            sentenca = SentencaUsuario(
                nome_arquivo=filename,
                texto_extraido=text,
                caracteristicas_estilo=json.dumps(style_analysis, ensure_ascii=False)
            )
            
            db.session.add(sentenca)
            db.session.commit()
            
            self.logger.info(f"Sentença processada com sucesso: {filename}")
            
            return {
                'success': True,
                'sentenca_id': sentenca.id,
                'text_length': len(text),
                'style_analysis': style_analysis
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Erro ao processar sentença {filename}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_multiple_pdfs(self, pdf_directory):
        """Processa múltiplos PDFs de um diretório"""
        results = {
            'processed': [],
            'errors': [],
            'total_processed': 0
        }
        
        try:
            if not os.path.exists(pdf_directory):
                raise ValueError("Diretório não encontrado")
            
            pdf_files = [f for f in os.listdir(pdf_directory) if f.lower().endswith('.pdf')]
            
            for pdf_file in pdf_files:
                pdf_path = os.path.join(pdf_directory, pdf_file)
                result = self.process_pdf_sentence(pdf_path, pdf_file)
                
                if result['success']:
                    results['processed'].append({
                        'filename': pdf_file,
                        'sentenca_id': result['sentenca_id'],
                        'text_length': result['text_length']
                    })
                    results['total_processed'] += 1
                else:
                    results['errors'].append({
                        'filename': pdf_file,
                        'error': result['error']
                    })
            
            self.logger.info(f"Processamento concluído: {results['total_processed']} sentenças processadas")
            
        except Exception as e:
            self.logger.error(f"Erro no processamento em lote: {e}")
            results['errors'].append({
                'filename': 'GERAL',
                'error': str(e)
            })
        
        return results
    
    def get_user_style_profile(self):
        """Cria um perfil de estilo baseado em todas as sentenças do usuário"""
        try:
            # Busca todas as sentenças do usuário
            sentencas = SentencaUsuario.query.all()
            
            if not sentencas:
                return {
                    'success': False,
                    'message': 'Nenhuma sentença encontrada para análise'
                }
            
            # Extrai análises de estilo
            analyses = []
            for sentenca in sentencas:
                if sentenca.caracteristicas_estilo:
                    try:
                        style_data = json.loads(sentenca.caracteristicas_estilo)
                        analyses.append(style_data)
                    except json.JSONDecodeError:
                        continue
            
            if not analyses:
                return {
                    'success': False,
                    'message': 'Nenhuma análise de estilo válida encontrada'
                }
            
            # Cria perfil agregado
            style_profile = self.style_analyzer.create_style_profile(analyses)
            
            return {
                'success': True,
                'profile': style_profile,
                'based_on_sentences': len(analyses),
                'total_sentences': len(sentencas)
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao criar perfil de estilo: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_sentences_summary(self):
        """Retorna resumo das sentenças processadas"""
        try:
            sentencas = SentencaUsuario.query.all()
            
            summary = {
                'total_sentences': len(sentencas),
                'sentences': []
            }
            
            for sentenca in sentencas:
                sentence_info = {
                    'id': sentenca.id,
                    'filename': sentenca.nome_arquivo,
                    'text_length': len(sentenca.texto_extraido),
                    'upload_date': sentenca.data_upload.isoformat() if sentenca.data_upload else None,
                    'has_style_analysis': bool(sentenca.caracteristicas_estilo)
                }
                summary['sentences'].append(sentence_info)
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Erro ao obter resumo: {e}")
            return {'total_sentences': 0, 'sentences': []}
    
    def delete_sentence(self, sentence_id):
        """Remove uma sentença do banco de dados"""
        try:
            sentenca = SentencaUsuario.query.get(sentence_id)
            if not sentenca:
                return {
                    'success': False,
                    'message': 'Sentença não encontrada'
                }
            
            filename = sentenca.nome_arquivo
            db.session.delete(sentenca)
            db.session.commit()
            
            self.logger.info(f"Sentença removida: {filename}")
            
            return {
                'success': True,
                'message': f'Sentença {filename} removida com sucesso'
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Erro ao remover sentença: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def reanalyze_sentence(self, sentence_id):
        """Reanalisa o estilo de uma sentença específica"""
        try:
            sentenca = SentencaUsuario.query.get(sentence_id)
            if not sentenca:
                return {
                    'success': False,
                    'message': 'Sentença não encontrada'
                }
            
            # Reanalisa o estilo
            style_analysis = self.style_analyzer.analyze_text_style(sentenca.texto_extraido)
            
            # Atualiza no banco
            sentenca.caracteristicas_estilo = json.dumps(style_analysis, ensure_ascii=False)
            db.session.commit()
            
            self.logger.info(f"Sentença reanalisada: {sentenca.nome_arquivo}")
            
            return {
                'success': True,
                'style_analysis': style_analysis
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Erro ao reanalizar sentença: {e}")
            return {
                'success': False,
                'error': str(e)
            }

