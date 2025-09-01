from flask import Blueprint, request, jsonify, current_app
import logging

scheduler_bp = Blueprint('scheduler', __name__)
logger = logging.getLogger(__name__)

@scheduler_bp.route('/status', methods=['GET'])
def get_scheduler_status():
    """Endpoint para verificar status do scheduler"""
    try:
        scheduler_service = current_app.scheduler_service
        status = scheduler_service.get_scheduler_status()
        
        return jsonify({
            'success': True,
            'status': status
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter status do scheduler: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@scheduler_bp.route('/jobs', methods=['GET'])
def get_scheduled_jobs():
    """Endpoint para listar jobs agendados"""
    try:
        scheduler_service = current_app.scheduler_service
        jobs = scheduler_service.get_scheduled_jobs()
        
        return jsonify({
            'success': True,
            'jobs': jobs,
            'count': len(jobs)
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter jobs: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@scheduler_bp.route('/jobs/<job_id>/run', methods=['POST'])
def run_job_now(job_id):
    """Endpoint para executar um job imediatamente"""
    try:
        scheduler_service = current_app.scheduler_service
        result = scheduler_service.run_job_now(job_id)
        
        return jsonify(result), 200 if result.get('success') else 400
        
    except Exception as e:
        logger.error(f"Erro ao executar job {job_id}: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@scheduler_bp.route('/jobs/<job_id>', methods=['DELETE'])
def remove_job(job_id):
    """Endpoint para remover um job agendado"""
    try:
        # Protege job principal
        if job_id == 'daily_jurisprudence':
            return jsonify({
                'success': False,
                'message': 'Não é possível remover o job principal de coleta diária'
            }), 400
        
        scheduler_service = current_app.scheduler_service
        result = scheduler_service.remove_job(job_id)
        
        return jsonify(result), 200 if result.get('success') else 400
        
    except Exception as e:
        logger.error(f"Erro ao remover job {job_id}: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@scheduler_bp.route('/collect-now', methods=['POST'])
def collect_jurisprudence_now():
    """Endpoint para executar coleta de jurisprudência imediatamente"""
    try:
        data = request.get_json() or {}
        days_back = data.get('days_back', 1)
        
        scheduler_service = current_app.scheduler_service
        
        # Executa coleta com contexto da aplicação
        with current_app.app_context():
            from src.services.jurisprudencia_service import JurisprudenciaService
            service = JurisprudenciaService()
            results = service.collect_all_recent_jurisprudence(days_back)
        
        return jsonify({
            'success': True,
            'message': f'Coleta executada: {results["total_collected"]} itens coletados',
            'results': results
        }), 200
        
    except Exception as e:
        logger.error(f"Erro na coleta manual: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@scheduler_bp.route('/schedule-config', methods=['GET'])
def get_schedule_config():
    """Endpoint para obter configuração do agendamento"""
    try:
        return jsonify({
            'success': True,
            'config': {
                'daily_collection_time': '09:00',
                'timezone': 'America/Sao_Paulo',
                'description': 'Coleta diária de jurisprudência às 9h (horário de Brasília)',
                'sources': [
                    'STF - Supremo Tribunal Federal',
                    'STJ - Superior Tribunal de Justiça', 
                    'TST - Tribunal Superior do Trabalho',
                    'TSE - Tribunal Superior Eleitoral',
                    'STM - Superior Tribunal Militar',
                    'TJSP - Tribunal de Justiça de São Paulo',
                    'FONAJE - Enunciados dos Juizados Especiais',
                    'CNJ - Enunciados do Conselho Nacional de Justiça'
                ]
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter configuração: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@scheduler_bp.route('/schedule-config', methods=['PUT'])
def update_schedule_config():
    """Endpoint para atualizar configuração do agendamento"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'Dados de configuração são obrigatórios'
            }), 400
        
        # Valida horário
        hour = data.get('hour')
        minute = data.get('minute', 0)
        
        if hour is None or not (0 <= hour <= 23):
            return jsonify({
                'success': False,
                'message': 'Hora deve estar entre 0 e 23'
            }), 400
        
        if not (0 <= minute <= 59):
            return jsonify({
                'success': False,
                'message': 'Minuto deve estar entre 0 e 59'
            }), 400
        
        scheduler_service = current_app.scheduler_service
        
        # Remove job atual
        scheduler_service.remove_job('daily_jurisprudence')
        
        # Adiciona novo job com horário atualizado
        from apscheduler.triggers.cron import CronTrigger
        import pytz
        
        timezone = pytz.timezone('America/Sao_Paulo')
        scheduler_service.scheduler.add_job(
            func=scheduler_service.collect_daily_jurisprudence,
            trigger=CronTrigger(hour=hour, minute=minute, timezone=timezone),
            id='daily_jurisprudence',
            name='Coleta Diária de Jurisprudência',
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=3600
        )
        
        return jsonify({
            'success': True,
            'message': f'Agendamento atualizado para {hour:02d}:{minute:02d}',
            'new_schedule': f'{hour:02d}:{minute:02d}'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao atualizar configuração: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

