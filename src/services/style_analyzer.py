import re
import json
import logging
from collections import Counter
import textstat
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np

# Download de recursos do NLTK necessários
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger')

class StyleAnalyzer:
    """Serviço para análise de estilo de escrita jurídica"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.stopwords = set(nltk.corpus.stopwords.words('portuguese'))
        
        # Termos jurídicos comuns
        self.legal_terms = {
            'procedimentais': ['processo', 'autos', 'petição', 'contestação', 'réplica', 'tréplica', 
                              'audiência', 'despacho', 'decisão', 'sentença', 'acórdão'],
            'substantivos': ['direito', 'lei', 'código', 'artigo', 'parágrafo', 'inciso', 'alínea',
                           'jurisprudência', 'precedente', 'súmula', 'enunciado'],
            'processuais': ['autor', 'réu', 'requerente', 'requerido', 'apelante', 'apelado',
                          'recorrente', 'recorrido', 'embargante', 'embargado'],
            'decisorios': ['julgo', 'decido', 'determino', 'defiro', 'indefiro', 'homologo',
                         'condeno', 'absolvo', 'reconheço', 'declaro']
        }
    
    def analyze_text_style(self, text):
        """Analisa o estilo de escrita de um texto"""
        if not text or len(text.strip()) < 100:
            return {}
        
        try:
            analysis = {
                'readability': self._analyze_readability(text),
                'sentence_structure': self._analyze_sentence_structure(text),
                'vocabulary': self._analyze_vocabulary(text),
                'legal_language': self._analyze_legal_language(text),
                'writing_patterns': self._analyze_writing_patterns(text),
                'formality': self._analyze_formality(text),
                'argumentation': self._analyze_argumentation_style(text)
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Erro na análise de estilo: {e}")
            return {}
    
    def _analyze_readability(self, text):
        """Analisa a legibilidade do texto"""
        try:
            # Adapta métricas para português
            sentences = nltk.sent_tokenize(text, language='portuguese')
            words = nltk.word_tokenize(text, language='portuguese')
            
            # Métricas básicas
            avg_sentence_length = len(words) / len(sentences) if sentences else 0
            avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
            
            # Flesch Reading Ease (adaptado)
            flesch_score = textstat.flesch_reading_ease(text)
            
            return {
                'avg_sentence_length': round(avg_sentence_length, 2),
                'avg_word_length': round(avg_word_length, 2),
                'flesch_score': flesch_score,
                'total_sentences': len(sentences),
                'total_words': len(words)
            }
            
        except Exception as e:
            self.logger.error(f"Erro na análise de legibilidade: {e}")
            return {}
    
    def _analyze_sentence_structure(self, text):
        """Analisa a estrutura das sentenças"""
        try:
            sentences = nltk.sent_tokenize(text, language='portuguese')
            
            # Classifica sentenças por comprimento
            short_sentences = [s for s in sentences if len(s.split()) <= 15]
            medium_sentences = [s for s in sentences if 15 < len(s.split()) <= 30]
            long_sentences = [s for s in sentences if len(s.split()) > 30]
            
            # Analisa tipos de pontuação
            exclamations = len(re.findall(r'!', text))
            questions = len(re.findall(r'\?', text))
            semicolons = len(re.findall(r';', text))
            colons = len(re.findall(r':', text))
            
            return {
                'sentence_length_distribution': {
                    'short': len(short_sentences),
                    'medium': len(medium_sentences),
                    'long': len(long_sentences)
                },
                'punctuation_usage': {
                    'exclamations': exclamations,
                    'questions': questions,
                    'semicolons': semicolons,
                    'colons': colons
                }
            }
            
        except Exception as e:
            self.logger.error(f"Erro na análise de estrutura: {e}")
            return {}
    
    def _analyze_vocabulary(self, text):
        """Analisa o vocabulário utilizado"""
        try:
            words = nltk.word_tokenize(text.lower(), language='portuguese')
            words = [word for word in words if word.isalpha() and word not in self.stopwords]
            
            # Diversidade lexical
            unique_words = set(words)
            lexical_diversity = len(unique_words) / len(words) if words else 0
            
            # Palavras mais frequentes
            word_freq = Counter(words)
            most_common = word_freq.most_common(20)
            
            # Comprimento médio das palavras
            avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
            
            return {
                'lexical_diversity': round(lexical_diversity, 3),
                'total_unique_words': len(unique_words),
                'avg_word_length': round(avg_word_length, 2),
                'most_common_words': most_common[:10]
            }
            
        except Exception as e:
            self.logger.error(f"Erro na análise de vocabulário: {e}")
            return {}
    
    def _analyze_legal_language(self, text):
        """Analisa o uso de linguagem jurídica"""
        try:
            text_lower = text.lower()
            legal_usage = {}
            
            for category, terms in self.legal_terms.items():
                count = sum(len(re.findall(rf'\b{term}\b', text_lower)) for term in terms)
                legal_usage[category] = count
            
            # Identifica citações de leis e artigos
            law_citations = len(re.findall(r'lei\s+n[ºº]?\s*\d+', text_lower))
            article_citations = len(re.findall(r'art\.?\s*\d+', text_lower))
            code_citations = len(re.findall(r'código\s+\w+', text_lower))
            
            # Expressões latinas comuns no direito
            latin_expressions = [
                'ad hoc', 'a priori', 'a posteriori', 'ex officio', 'in dubio pro reo',
                'pacta sunt servanda', 'res judicata', 'ultra petita', 'citra petita'
            ]
            latin_count = sum(len(re.findall(rf'\b{expr}\b', text_lower)) for expr in latin_expressions)
            
            return {
                'legal_terms_usage': legal_usage,
                'citations': {
                    'laws': law_citations,
                    'articles': article_citations,
                    'codes': code_citations
                },
                'latin_expressions': latin_count
            }
            
        except Exception as e:
            self.logger.error(f"Erro na análise de linguagem jurídica: {e}")
            return {}
    
    def _analyze_writing_patterns(self, text):
        """Analisa padrões de escrita"""
        try:
            # Uso de voz passiva (aproximação)
            passive_voice = len(re.findall(r'\b(foi|foram|será|serão|sendo|sido)\s+\w+[ado|ida]', text.lower()))
            
            # Uso de primeira pessoa
            first_person = len(re.findall(r'\b(eu|meu|minha|meus|minhas|comigo)\b', text.lower()))
            
            # Uso de conectivos
            connectives = [
                'portanto', 'contudo', 'entretanto', 'todavia', 'assim', 'dessa forma',
                'por conseguinte', 'ademais', 'outrossim', 'destarte'
            ]
            connective_count = sum(len(re.findall(rf'\b{conn}\b', text.lower())) for conn in connectives)
            
            # Uso de advérbios de modo
            adverbs = len(re.findall(r'\w+mente\b', text.lower()))
            
            return {
                'passive_voice_usage': passive_voice,
                'first_person_usage': first_person,
                'connectives_usage': connective_count,
                'adverbs_usage': adverbs
            }
            
        except Exception as e:
            self.logger.error(f"Erro na análise de padrões: {e}")
            return {}
    
    def _analyze_formality(self, text):
        """Analisa o nível de formalidade"""
        try:
            # Indicadores de formalidade
            formal_indicators = [
                'vossa excelência', 'meritíssimo', 'ilustríssimo', 'egrégio',
                'colendo', 'respeitosamente', 'cordialmente'
            ]
            
            formality_score = sum(len(re.findall(rf'\b{indicator}\b', text.lower())) 
                                for indicator in formal_indicators)
            
            # Contrações (indicam informalidade)
            contractions = len(re.findall(r'\b(não|num|numa|nuns|numas|do|da|dos|das)\b', text.lower()))
            
            return {
                'formality_score': formality_score,
                'contractions': contractions,
                'formality_level': 'high' if formality_score > 5 else 'medium' if formality_score > 2 else 'low'
            }
            
        except Exception as e:
            self.logger.error(f"Erro na análise de formalidade: {e}")
            return {}
    
    def _analyze_argumentation_style(self, text):
        """Analisa o estilo de argumentação"""
        try:
            # Palavras que indicam argumentação
            argument_indicators = [
                'porque', 'pois', 'uma vez que', 'visto que', 'considerando',
                'tendo em vista', 'diante do exposto', 'ante o exposto'
            ]
            
            argumentation_count = sum(len(re.findall(rf'\b{indicator}\b', text.lower())) 
                                    for indicator in argument_indicators)
            
            # Uso de precedentes
            precedent_indicators = [
                'jurisprudência', 'precedente', 'súmula', 'entendimento',
                'orientação', 'posicionamento'
            ]
            
            precedent_usage = sum(len(re.findall(rf'\b{indicator}\b', text.lower())) 
                                for indicator in precedent_indicators)
            
            return {
                'argumentation_density': argumentation_count,
                'precedent_usage': precedent_usage,
                'argumentation_style': 'analytical' if argumentation_count > 10 else 'direct'
            }
            
        except Exception as e:
            self.logger.error(f"Erro na análise de argumentação: {e}")
            return {}
    
    def create_style_profile(self, analyses):
        """Cria um perfil de estilo baseado em múltiplas análises"""
        if not analyses:
            return {}
        
        try:
            # Agrega características de múltiplos textos
            profile = {
                'avg_sentence_length': np.mean([a.get('readability', {}).get('avg_sentence_length', 0) for a in analyses]),
                'avg_word_length': np.mean([a.get('readability', {}).get('avg_word_length', 0) for a in analyses]),
                'lexical_diversity': np.mean([a.get('vocabulary', {}).get('lexical_diversity', 0) for a in analyses]),
                'formality_level': Counter([a.get('formality', {}).get('formality_level', 'medium') for a in analyses]).most_common(1)[0][0],
                'argumentation_style': Counter([a.get('argumentation', {}).get('argumentation_style', 'direct') for a in analyses]).most_common(1)[0][0],
                'legal_language_intensity': np.mean([sum(a.get('legal_language', {}).get('legal_terms_usage', {}).values()) for a in analyses]),
                'passive_voice_tendency': np.mean([a.get('writing_patterns', {}).get('passive_voice_usage', 0) for a in analyses]),
                'connectives_usage': np.mean([a.get('writing_patterns', {}).get('connectives_usage', 0) for a in analyses])
            }
            
            return profile
            
        except Exception as e:
            self.logger.error(f"Erro ao criar perfil de estilo: {e}")
            return {}

