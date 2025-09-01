from flask import Blueprint, request, jsonify
from src.services.jurisprudencia_service import JurisprudenciaService
import logging

jurisprudencia_bp = Blueprint('jurisprudencia', __name__)
logger = logging.getLogger(__name__)

@jurisprudencia_bp.route('/collect', methods=['POST'])
def collect_jurisprudence():
    """Endpoint para coletar jurisprudência recente"""
    try:
        data = request.get_json() or {}
        days_back = data.get('days_back', 7)
        
        service = JurisprudenciaService()
        results = service.collect_all_recent_jurisprudence(days_back)
        
        return jsonify({
            'success': True,
            'message': f'Coleta finalizada. {results["total_collected"]} itens coletados.',
            'results': results
        }), 200
        
    except Exception as e:
        logger.error(f"Erro na coleta de jurisprudência: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro na coleta: {str(e)}'
        }), 500

@jurisprudencia_bp.route('/recent', methods=['GET'])
def get_recent_jurisprudence():
    """Endpoint para buscar jurisprudência recente"""
    try:
        tribunal = request.args.get('tribunal')
        limit = int(request.args.get('limit', 50))
        
        service = JurisprudenciaService()
        jurisprudencia = service.get_recent_jurisprudence(tribunal, limit)
        
        return jsonify({
            'success': True,
            'data': jurisprudencia,
            'count': len(jurisprudencia)
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao buscar jurisprudência: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro na busca: {str(e)}'
        }), 500

@jurisprudencia_bp.route('/search', methods=['GET'])
def search_jurisprudence():
    """Endpoint para buscar jurisprudência por termo"""
    try:
        search_term = request.args.get('q', '')
        tribunal = request.args.get('tribunal')
        limit = int(request.args.get('limit', 50))
        
        if not search_term:
            return jsonify({
                'success': False,
                'message': 'Termo de busca é obrigatório'
            }), 400
        
        service = JurisprudenciaService()
        jurisprudencia = service.search_jurisprudence(search_term, tribunal, limit)
        
        return jsonify({
            'success': True,
            'data': jurisprudencia,
            'count': len(jurisprudencia),
            'search_term': search_term
        }), 200
        
    except Exception as e:
        logger.error(f"Erro na busca de jurisprudência: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro na busca: {str(e)}'
        }), 500

@jurisprudencia_bp.route('/enunciados', methods=['GET'])
def get_enunciados():
    """Endpoint para buscar enunciados"""
    try:
        orgao = request.args.get('orgao')  # FONAJE ou CNJ
        tipo = request.args.get('tipo')    # CIVEL, CRIMINAL, FAZENDA_PUBLICA
        limit = int(request.args.get('limit', 100))
        
        service = JurisprudenciaService()
        enunciados = service.get_enunciados(orgao, tipo, limit)
        
        return jsonify({
            'success': True,
            'data': enunciados,
            'count': len(enunciados)
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao buscar enunciados: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro na busca: {str(e)}'
        }), 500

@jurisprudencia_bp.route('/status', methods=['GET'])
def get_status():
    """Endpoint para verificar status do sistema"""
    try:
        service = JurisprudenciaService()
        
        # Conta registros por tribunal
        status = {}
        for tribunal in ['STF', 'STJ', 'TST', 'TSE', 'STM', 'TJSP']:
            jurisprudencia = service.get_recent_jurisprudence(tribunal, 1000)
            status[tribunal] = len(jurisprudencia)
        
        # Conta enunciados
        enunciados_fonaje = service.get_enunciados('FONAJE', None, 1000)
        enunciados_cnj = service.get_enunciados('CNJ', None, 1000)
        
        status['ENUNCIADOS'] = {
            'FONAJE': len(enunciados_fonaje),
            'CNJ': len(enunciados_cnj)
        }
        
        return jsonify({
            'success': True,
            'status': status
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao verificar status: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro ao verificar status: {str(e)}'
        }), 500

