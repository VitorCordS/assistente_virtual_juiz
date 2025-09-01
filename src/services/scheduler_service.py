import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from src.services.jurisprudencia_service import JurisprudenciaService

class SchedulerService:
    """Serviço para agendamento de tarefas automáticas"""
    
    def __init__(self, app=None):
        self.logger = logging.getLogger(__name__)
        self.scheduler = None
        self.app = app
        self.timezone = pytz.timezone('America/Sao_Paulo')  # Horário de Brasília
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializa o scheduler com a aplicação Flask"""
        self.app = app
        
        # Configura o scheduler
        self.scheduler = BackgroundScheduler(timezone=self.timezone)
        
        # Adiciona job de coleta diária
        self.add_daily_jurisprudence_job()
        
        # Inicia o scheduler
        self.start_scheduler()
        
        # Registra função de limpeza ao encerrar a aplicação
        import atexit
        atexit.register(self.shutdown_scheduler)
    
    def add_daily_jurisprudence_job(self):
        """Adiciona job para coleta diária de jurisprudência às 9h"""
        try:
            # Remove job existente se houver
            if self.scheduler.get_job('daily_jurisprudence'):
                self.scheduler.remove_job('daily_jurisprudence')
            
            # Adiciona novo job
            self.scheduler.add_job(
                func=self.collect_daily_jurisprudence,
                trigger=CronTrigger(hour=9, minute=0, timezone=self.timezone),
                id='daily_jurisprudence',
                name='Coleta Diária de Jurisprudência',
                replace_existing=True,
                max_instances=1,
                misfire_grace_time=3600  # 1 hora de tolerância
            )
            
            self.logger.info("Job de coleta diária configurado para 9h (horário de Brasília)")
            
        except Exception as e:
            self.logger.error(f"Erro ao configurar job diário: {e}")
    
    def collect_daily_jurisprudence(self):
        """Função executada diariamente para coletar jurisprudência"""
        try:
            self.logger.info("Iniciando coleta diária de jurisprudência")
            
            # Cria contexto da aplicação Flask
            with self.app.app_context():
                service = JurisprudenciaService()
                results = service.collect_all_recent_jurisprudence(days_back=1)
                
                self.logger.info(f"Coleta diária concluída: {results['total_collected']} itens coletados")
                
                # Log dos resultados
                for success_msg in results['success']:
                    self.logger.info(success_msg)
                
                for error_msg in results['errors']:
                    self.logger.error(error_msg)
                
                return results
                
        except Exception as e:
            self.logger.error(f"Erro na coleta diária: {e}")
            return {'error': str(e)}
    
    def start_scheduler(self):
        """Inicia o scheduler"""
        try:
            if self.scheduler and not self.scheduler.running:
                self.scheduler.start()
                self.logger.info("Scheduler iniciado com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar scheduler: {e}")
    
    def shutdown_scheduler(self):
        """Para o scheduler"""
        try:
            if self.scheduler and self.scheduler.running:
                self.scheduler.shutdown(wait=False)
                self.logger.info("Scheduler encerrado")
            
        except Exception as e:
            self.logger.error(f"Erro ao encerrar scheduler: {e}")
    
    def get_scheduled_jobs(self):
        """Retorna lista de jobs agendados"""
        try:
            if not self.scheduler:
                return []
            
            jobs = []
            for job in self.scheduler.get_jobs():
                job_info = {
                    'id': job.id,
                    'name': job.name,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger),
                    'func': job.func.__name__ if job.func else None
                }
                jobs.append(job_info)
            
            return jobs
            
        except Exception as e:
            self.logger.error(f"Erro ao obter jobs: {e}")
            return []
    
    def run_job_now(self, job_id):
        """Executa um job imediatamente"""
        try:
            if not self.scheduler:
                return {'success': False, 'message': 'Scheduler não inicializado'}
            
            job = self.scheduler.get_job(job_id)
            if not job:
                return {'success': False, 'message': 'Job não encontrado'}
            
            # Executa o job
            if job_id == 'daily_jurisprudence':
                with self.app.app_context():
                    results = self.collect_daily_jurisprudence()
                    return {'success': True, 'results': results}
            
            return {'success': False, 'message': 'Job não suportado para execução manual'}
            
        except Exception as e:
            self.logger.error(f"Erro ao executar job {job_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def add_custom_job(self, func, trigger_config, job_id, name):
        """Adiciona um job customizado"""
        try:
            # Remove job existente se houver
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            
            # Configura trigger baseado no tipo
            if trigger_config['type'] == 'cron':
                trigger = CronTrigger(
                    hour=trigger_config.get('hour', 0),
                    minute=trigger_config.get('minute', 0),
                    timezone=self.timezone
                )
            else:
                raise ValueError(f"Tipo de trigger não suportado: {trigger_config['type']}")
            
            # Adiciona job
            self.scheduler.add_job(
                func=func,
                trigger=trigger,
                id=job_id,
                name=name,
                replace_existing=True,
                max_instances=1
            )
            
            self.logger.info(f"Job customizado adicionado: {name}")
            return {'success': True, 'message': f'Job {name} adicionado com sucesso'}
            
        except Exception as e:
            self.logger.error(f"Erro ao adicionar job customizado: {e}")
            return {'success': False, 'error': str(e)}
    
    def remove_job(self, job_id):
        """Remove um job agendado"""
        try:
            if not self.scheduler:
                return {'success': False, 'message': 'Scheduler não inicializado'}
            
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                self.logger.info(f"Job removido: {job_id}")
                return {'success': True, 'message': f'Job {job_id} removido com sucesso'}
            else:
                return {'success': False, 'message': 'Job não encontrado'}
            
        except Exception as e:
            self.logger.error(f"Erro ao remover job {job_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_scheduler_status(self):
        """Retorna status do scheduler"""
        try:
            if not self.scheduler:
                return {
                    'running': False,
                    'jobs_count': 0,
                    'timezone': str(self.timezone),
                    'current_time': datetime.now(self.timezone).isoformat()
                }
            
            return {
                'running': self.scheduler.running,
                'jobs_count': len(self.scheduler.get_jobs()),
                'timezone': str(self.timezone),
                'current_time': datetime.now(self.timezone).isoformat(),
                'next_daily_collection': self._get_next_daily_collection_time()
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao obter status: {e}")
            return {'error': str(e)}
    
    def _get_next_daily_collection_time(self):
        """Retorna o próximo horário de coleta diária"""
        try:
            job = self.scheduler.get_job('daily_jurisprudence')
            if job and job.next_run_time:
                return job.next_run_time.isoformat()
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao obter próximo horário: {e}")
            return None

