import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from src.services.sentence_service import SentenceService
import logging

sentences_bp = Blueprint('sentences', __name__)
logger = logging.getLogger(__name__)

# Configurações de upload
ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@sentences_bp.route('/upload', methods=['POST'])
def upload_sentence():
    """Endpoint para upload de sentença em PDF"""
    try:
        # Verifica se há arquivo na requisição
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'Nenhum arquivo enviado'
            }), 400
        
        file = request.files['file']
        
        # Verifica se arquivo foi selecionado
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'Nenhum arquivo selecionado'
            }), 400
        
        # Verifica extensão
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'message': 'Apenas arquivos PDF são permitidos'
            }), 400
        
        # Verifica tamanho do arquivo
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({
                'success': False,
                'message': 'Arquivo muito grande. Máximo permitido: 16MB'
            }), 400
        
        # Salva arquivo temporariamente
        filename = secure_filename(file.filename)
        upload_dir = os.path.join(current_app.root_path, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        try:
            # Processa o PDF
            with current_app.app_context():
                service = SentenceService()
                result = service.process_pdf_sentence(file_path, filename)            
            # Remove arquivo temporário
            os.remove(file_path)
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'message': 'Sentença processada com sucesso',
                    'data': {
                        'sentenca_id': result['sentenca_id'],
                        'text_length': result['text_length'],
                        'filename': filename
                    }
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': f'Erro ao processar PDF: {result["error"]}'
                }), 500
                
        except Exception as e:
            # Remove arquivo temporário em caso de erro
            if os.path.exists(file_path):
                os.remove(file_path)
            raise e
        
    except Exception as e:
        logger.error(f"Erro no upload de sentença: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@sentences_bp.route('/upload-multiple', methods=['POST'])
def upload_multiple_sentences():
    """Endpoint para upload múltiplo de sentenças"""
    try:
        # Verifica se há arquivos na requisição
        if 'files' not in request.files:
            return jsonify({
                'success': False,
                'message': 'Nenhum arquivo enviado'
            }), 400
        
        files = request.files.getlist('files')
        
        if not files or all(f.filename == '' for f in files):
            return jsonify({
                'success': False,
                'message': 'Nenhum arquivo selecionado'
            }), 400
        
        # Cria diretório temporário
        upload_dir = os.path.join(current_app.root_path, 'uploads', 'batch')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Salva todos os arquivos
        saved_files = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(upload_dir, filename)
                file.save(file_path)
                saved_files.append(file_path)
        
        if not saved_files:
            return jsonify({
                'success': False,
                'message': 'Nenhum arquivo PDF válido encontrado'
            }), 400
        
        try:
            # Processa todos os PDFs
            with current_app.app_context():
                service = SentenceService()
                results = service.process_multiple_pdfs(upload_dir)            
            # Remove arquivos temporários
            for file_path in saved_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            return jsonify({
                'success': True,
                'message': f'{results["total_processed"]} sentenças processadas com sucesso',
                'results': results
            }), 200
            
        except Exception as e:
            # Remove arquivos temporários em caso de erro
            for file_path in saved_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
            raise e
        
    except Exception as e:
        logger.error(f"Erro no upload múltiplo: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@sentences_bp.route('/list', methods=['GET'])
def list_sentences():
    """Endpoint para listar sentenças processadas"""
    try:
        with current_app.app_context():
            service = SentenceService()
            summary = service.get_sentences_summary()
        
        return jsonify({
            'success': True,
            'data': summary
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar sentenças: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@sentences_bp.route('/style-profile', methods=['GET'])
def get_style_profile():
    """Endpoint para obter perfil de estilo do usuário"""
    try:
        service = SentenceService()
        profile = service.get_user_style_profile()
        
        return jsonify(profile), 200 if profile.get('success') else 400
        
    except Exception as e:
        logger.error(f"Erro ao obter perfil de estilo: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@sentences_bp.route('/<int:sentence_id>', methods=['DELETE'])
def delete_sentence(sentence_id):
    """Endpoint para remover uma sentença"""
    try:
        service = SentenceService()
        result = service.delete_sentence(sentence_id)
        
        return jsonify(result), 200 if result.get('success') else 400
        
    except Exception as e:
        logger.error(f"Erro ao remover sentença: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@sentences_bp.route('/<int:sentence_id>/reanalyze', methods=['POST'])
def reanalyze_sentence(sentence_id):
    """Endpoint para reanalizar uma sentença"""
    try:
        service = SentenceService()
        result = service.reanalyze_sentence(sentence_id)
        
        return jsonify(result), 200 if result.get('success') else 400
        
    except Exception as e:
        logger.error(f"Erro ao reanalizar sentença: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@sentences_bp.route('/clear-all', methods=['DELETE'])
def clear_all_sentences():
    """Endpoint para remover todas as sentenças"""
    try:
        service = SentenceService()
        
        # Busca todas as sentenças
        summary = service.get_sentences_summary()
        sentence_ids = [s['id'] for s in summary['sentences']]
        
        # Remove uma por uma
        removed_count = 0
        for sentence_id in sentence_ids:
            result = service.delete_sentence(sentence_id)
            if result.get('success'):
                removed_count += 1
        
        return jsonify({
            'success': True,
            'message': f'{removed_count} sentenças removidas',
            'removed_count': removed_count
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao limpar sentenças: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

