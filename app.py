#!/usr/bin/env python3
"""
Avaliador Automático de Programas Python
Versão 3.0 - Completa
- Sistema de utilizadores
- Análise estática melhorada
- Dicas inteligentes
- Editor com syntax highlighting
- Exportar PDF
- Modo professor expandido
"""

import streamlit as st
import json
import os
import re
import time
import base64
from datetime import datetime
import requests
from io import BytesIO

# =============================================================================
# CONFIGURAÇÃO SUPABASE
# =============================================================================

SUPABASE_URL = "https://jssnogllerzeezgeodxy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Impzc25vZ2xsZXJ6ZWV6Z2VvZHh5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjUyMzU4NTksImV4cCI6MjA4MDgxMTg1OX0.6DAaTeFLkLNDOeZsjS93ee53z5wvncHKAFlY046Cw6s"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

HEADERS_RETURN = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# =============================================================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================================================

st.set_page_config(
    page_title="Avaliador Python v3.0",
    page_icon="🐍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CSS PERSONALIZADO
# =============================================================================

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #8b5cf6 100%);
        color: white;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
    }
    .user-badge {
        background: linear-gradient(90deg, #10b981, #059669);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
    }
    .professor-badge {
        background: linear-gradient(90deg, #8b5cf6, #7c3aed);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
    }
    .score-approved {
        font-size: 2.5rem;
        color: #10b981;
        font-weight: bold;
        text-align: center;
    }
    .score-failed {
        font-size: 2.5rem;
        color: #ef4444;
        font-weight: bold;
        text-align: center;
    }
    .hint-box {
        background: linear-gradient(90deg, #fef3c7, #fde68a);
        border-left: 4px solid #f59e0b;
        padding: 1rem;
        border-radius: 0 10px 10px 0;
        margin: 0.5rem 0;
    }
    .analysis-card {
        background: #f0f9ff;
        border: 1px solid #bae6fd;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .security-alert {
        background: #fef2f2;
        border-left: 4px solid #ef4444;
        padding: 1rem;
        border-radius: 0 10px 10px 0;
    }
    .style-warning {
        background: #fffbeb;
        border-left: 4px solid #f59e0b;
        padding: 0.5rem 1rem;
        border-radius: 0 8px 8px 0;
        font-size: 0.9rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    .exercise-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        transition: all 0.3s;
    }
    .exercise-card:hover {
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-color: #3b82f6;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# FUNÇÕES SUPABASE
# =============================================================================

def db_login(username, password):
    url = f"{SUPABASE_URL}/rest/v1/users?username=eq.{username}&password=eq.{password}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        users = response.json()
        if users:
            return users[0]
    return None


def db_register(username, password, role="aluno"):
    url = f"{SUPABASE_URL}/rest/v1/users?username=eq.{username}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200 and response.json():
        return None, "Username já existe"
    
    url = f"{SUPABASE_URL}/rest/v1/users"
    data = {"username": username, "password": password, "role": role}
    response = requests.post(url, headers=HEADERS_RETURN, json=data)
    
    if response.status_code == 201:
        return True, "Conta criada com sucesso!"
    return None, "Erro ao criar conta"


def db_save_submission(user_id, username, exercise_id, exercise_title, code, score, tests_passed, tests_total, status):
    url = f"{SUPABASE_URL}/rest/v1/submissions"
    data = {
        "user_id": user_id,
        "username": username,
        "exercise_id": exercise_id,
        "exercise_title": exercise_title,
        "code": code,
        "score": float(score),
        "tests_passed": tests_passed,
        "tests_total": tests_total,
        "status": status
    }
    response = requests.post(url, headers=HEADERS, json=data)
    return response.status_code == 201


def db_get_user_submissions(username):
    url = f"{SUPABASE_URL}/rest/v1/submissions?username=eq.{username}&order=created_at.desc"
    response = requests.get(url, headers=HEADERS)
    return response.json() if response.status_code == 200 else []


def db_get_all_submissions():
    url = f"{SUPABASE_URL}/rest/v1/submissions?order=created_at.desc&limit=100"
    response = requests.get(url, headers=HEADERS)
    return response.json() if response.status_code == 200 else []


def db_get_all_users():
    url = f"{SUPABASE_URL}/rest/v1/users?order=created_at.desc"
    response = requests.get(url, headers=HEADERS)
    return response.json() if response.status_code == 200 else []


def db_delete_user(user_id):
    url = f"{SUPABASE_URL}/rest/v1/users?id=eq.{user_id}"
    response = requests.delete(url, headers=HEADERS)
    return response.status_code == 204


def db_get_user_stats(username):
    submissions = db_get_user_submissions(username)
    if not submissions:
        return {"total": 0, "approved": 0, "average": 0, "exercises_done": 0}
    
    total = len(submissions)
    approved = sum(1 for s in submissions if s.get('status') == 'approved')
    scores = [s.get('score', 0) for s in submissions if s.get('score') is not None]
    average = sum(scores) / len(scores) if scores else 0
    exercises_done = len(set(s.get('exercise_id') for s in submissions))
    
    return {"total": total, "approved": approved, "average": round(average, 1), "exercises_done": exercises_done}


# =============================================================================
# DICAS INTELIGENTES
# =============================================================================

SMART_HINTS = {
    "NameError": {
        "pattern": r"name '(\w+)' is not defined",
        "hints": [
            "💡 Variável '{match}' não existe. Verifica se a escreveste corretamente.",
            "💡 Esqueceste de definir '{match}' antes de a usar?",
            "💡 Atenção às maiúsculas/minúsculas: 'Var' é diferente de 'var'."
        ]
    },
    "IndentationError": {
        "pattern": r"",
        "hints": [
            "💡 Problema de indentação! Em Python, os espaços são importantes.",
            "💡 Usa sempre 4 espaços para indentar (não uses Tab).",
            "💡 Verifica se o código dentro de 'if', 'for', 'def' está indentado."
        ]
    },
    "SyntaxError": {
        "pattern": r"",
        "hints": [
            "💡 Erro de sintaxe! Verifica se não faltam ':' no fim de 'if', 'for', 'def'.",
            "💡 Verifica se todos os parênteses estão fechados.",
            "💡 Confirma que as strings têm aspas de abertura e fecho."
        ]
    },
    "TypeError": {
        "pattern": r"",
        "hints": [
            "💡 Estás a misturar tipos incompatíveis (ex: string + número).",
            "💡 Verifica se a função recebe o tipo de argumento correto.",
            "💡 Usa int(), str(), float() para converter tipos."
        ]
    },
    "RecursionError": {
        "pattern": r"",
        "hints": [
            "💡 Recursão infinita! A função chama-se a si mesma sem parar.",
            "💡 Verifica o caso base da recursão.",
            "💡 Garante que os argumentos mudam em cada chamada recursiva."
        ]
    },
    "ZeroDivisionError": {
        "pattern": r"",
        "hints": [
            "💡 Divisão por zero! Verifica o divisor antes de dividir.",
            "💡 Adiciona uma condição: 'if divisor != 0'"
        ]
    },
    "IndexError": {
        "pattern": r"",
        "hints": [
            "💡 Índice fora dos limites da lista!",
            "💡 Lembra-te: listas começam no índice 0.",
            "💡 Uma lista de 5 elementos tem índices 0, 1, 2, 3, 4."
        ]
    },
    "KeyError": {
        "pattern": r"",
        "hints": [
            "💡 Chave não existe no dicionário!",
            "💡 Usa .get('chave', valor_default) para evitar erros."
        ]
    },
    "function_not_defined": {
        "pattern": r"Função '(\w+)' não definida",
        "hints": [
            "💡 A função '{match}' não foi definida.",
            "💡 Verifica se o nome da função está correto.",
            "💡 A função deve chamar-se exatamente como pedido no exercício."
        ]
    },
    "no_return": {
        "pattern": r"",
        "hints": [
            "💡 A função retorna 'None'. Esqueceste do 'return'?",
            "💡 Verifica se tens 'return valor' no fim da função."
        ]
    },
    "wrong_result": {
        "pattern": r"",
        "hints": [
            "💡 O resultado está errado. Revê a lógica do algoritmo.",
            "💡 Testa manualmente com o input dado para entender o problema.",
            "💡 Verifica os casos limite (0, 1, valores negativos, listas vazias)."
        ]
    }
}


def get_smart_hint(error_msg, actual_result, expected_result):
    """Gera dicas inteligentes baseadas no erro."""
    hints = []
    
    if error_msg:
        for error_type, config in SMART_HINTS.items():
            if error_type in error_msg:
                pattern = config.get("pattern", "")
                match = ""
                if pattern:
                    m = re.search(pattern, error_msg)
                    if m:
                        match = m.group(1) if m.groups() else ""
                
                for hint in config["hints"][:2]:
                    hints.append(hint.format(match=match))
                break
    
    elif actual_result is None and expected_result is not None:
        hints.extend(SMART_HINTS["no_return"]["hints"][:2])
    
    elif actual_result != expected_result:
        hints.extend(SMART_HINTS["wrong_result"]["hints"][:2])
    
    return hints


# =============================================================================
# ANÁLISE ESTÁTICA MELHORADA
# =============================================================================

FORBIDDEN_KEYWORDS = [
    (r'\bimport\s+os\b', "import os - acesso ao sistema operativo"),
    (r'\bimport\s+sys\b', "import sys - acesso ao sistema"),
    (r'\bimport\s+subprocess\b', "import subprocess - execução de comandos"),
    (r'\bimport\s+socket\b', "import socket - acesso à rede"),
    (r'\bfrom\s+os\b', "from os - acesso ao sistema operativo"),
    (r'\bopen\s*\(', "open() - leitura/escrita de ficheiros"),
    (r'\beval\s*\(', "eval() - execução de código arbitrário"),
    (r'\bexec\s*\(', "exec() - execução de código arbitrário"),
    (r'\b__import__\s*\(', "__import__() - importação dinâmica"),
    (r'\bcompile\s*\(', "compile() - compilação de código"),
    (r'\bglobals\s*\(', "globals() - acesso a variáveis globais"),
    (r'\blocals\s*\(', "locals() - acesso a variáveis locais"),
]

SAFE_BUILTINS = {
    'abs': abs, 'all': all, 'any': any, 'bool': bool, 'chr': chr,
    'dict': dict, 'enumerate': enumerate, 'filter': filter, 'float': float,
    'frozenset': frozenset, 'int': int, 'isinstance': isinstance, 'len': len,
    'list': list, 'map': map, 'max': max, 'min': min, 'ord': ord, 'pow': pow,
    'print': print, 'range': range, 'reversed': reversed, 'round': round,
    'set': set, 'sorted': sorted, 'str': str, 'sum': sum, 'tuple': tuple,
    'zip': zip, 'True': True, 'False': False, 'None': None,
}


def analyze_security(code):
    """Análise de segurança do código."""
    issues = []
    for pattern, description in FORBIDDEN_KEYWORDS:
        if re.search(pattern, code):
            issues.append({"type": "security", "severity": "high", "message": f"⛔ Bloqueado: {description}"})
    return issues


def analyze_style(code):
    """Análise de estilo do código."""
    issues = []
    lines = code.split('\n')
    
    for i, line in enumerate(lines, 1):
        # Linhas muito longas
        if len(line) > 100:
            issues.append({"line": i, "severity": "medium", "message": f"Linha {i} muito longa ({len(line)} caracteres, máximo recomendado: 100)"})
        
        # Tabs em vez de espaços
        if '\t' in line:
            issues.append({"line": i, "severity": "low", "message": f"Linha {i}: usar espaços em vez de tabs"})
        
        # Espaços no fim da linha
        if line != line.rstrip() and line.strip():
            issues.append({"line": i, "severity": "low", "message": f"Linha {i}: espaços em branco no final"})
        
        # Múltiplos espaços
        if '  ' in line and not line.strip().startswith('#'):
            issues.append({"line": i, "severity": "low", "message": f"Linha {i}: múltiplos espaços consecutivos"})
    
    return issues[:15]


def analyze_code_quality(code):
    """Análise de qualidade do código."""
    issues = []
    
    # Encontrar variáveis definidas
    defined_vars = set(re.findall(r'(\w+)\s*=', code))
    
    # Encontrar variáveis usadas
    used_vars = set(re.findall(r'\b(\w+)\b', code)) - {'def', 'if', 'else', 'elif', 'for', 'while', 'return', 'and', 'or', 'not', 'in', 'True', 'False', 'None', 'pass', 'break', 'continue'}
    
    # Variáveis definidas mas não usadas (simplificado)
    # Esta é uma análise básica, não 100% precisa
    
    # Funções muito longas
    functions = re.findall(r'def\s+\w+[^:]+:(.+?)(?=\ndef|\Z)', code, re.DOTALL)
    for i, func_body in enumerate(functions):
        lines_count = len([l for l in func_body.split('\n') if l.strip()])
        if lines_count > 20:
            issues.append({"severity": "medium", "message": f"Função com {lines_count} linhas - considere dividir em funções menores"})
    
    # Complexidade ciclomática básica
    complexity_keywords = len(re.findall(r'\b(if|elif|else|for|while|and|or|try|except)\b', code))
    if complexity_keywords > 10:
        issues.append({"severity": "medium", "message": f"Complexidade alta ({complexity_keywords} estruturas de controlo)"})
    
    # Nomes de variáveis muito curtos
    short_vars = re.findall(r'\b([a-z])\s*=', code)
    for var in set(short_vars):
        if var not in ['i', 'j', 'k', 'n', 'x', 'y']:
            issues.append({"severity": "low", "message": f"Variável '{var}' tem nome muito curto - use nomes descritivos"})
    
    return issues[:10]


def analyze_complexity(code):
    """Métricas de complexidade."""
    lines = code.split('\n')
    code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
    
    return {
        "lines_total": len(lines),
        "lines_of_code": len(code_lines),
        "lines_comments": len([l for l in lines if l.strip().startswith('#')]),
        "num_functions": len(re.findall(r'\bdef\s+\w+', code)),
        "num_classes": len(re.findall(r'\bclass\s+\w+', code)),
        "num_loops": len(re.findall(r'\b(for|while)\b', code)),
        "num_conditionals": len(re.findall(r'\b(if|elif)\b', code)),
        "num_returns": len(re.findall(r'\breturn\b', code)),
        "complexity_score": len(re.findall(r'\b(if|elif|for|while|and|or)\b', code))
    }


def full_static_analysis(code):
    """Análise estática completa."""
    return {
        "security": analyze_security(code),
        "style": analyze_style(code),
        "quality": analyze_code_quality(code),
        "complexity": analyze_complexity(code)
    }


# =============================================================================
# MOTOR DE AVALIAÇÃO
# =============================================================================

def get_exercises_dir():
    return os.path.join(os.path.dirname(__file__), 'exercises')


def list_exercises():
    exercises_dir = get_exercises_dir()
    exercise_list = []
    if not os.path.exists(exercises_dir):
        return exercise_list
    for filename in os.listdir(exercises_dir):
        if filename.endswith(".json"):
            ex_id = filename.replace(".json", "")
            filepath = os.path.join(exercises_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    exercise = json.load(f)
                    exercise['id'] = ex_id
                    exercise_list.append(exercise)
            except:
                pass
    return sorted(exercise_list, key=lambda x: x.get('title', x['id']))


def load_exercise(ex_id):
    filepath = os.path.join(get_exercises_dir(), f"{ex_id}.json")
    with open(filepath, 'r', encoding='utf-8') as f:
        exercise = json.load(f)
        exercise['id'] = ex_id
        return exercise


def save_exercise(ex_id, exercise_data):
    """Guardar exercício (para modo professor)."""
    filepath = os.path.join(get_exercises_dir(), f"{ex_id}.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(exercise_data, f, indent=2, ensure_ascii=False)
    return True


def delete_exercise(ex_id):
    """Apagar exercício (para modo professor)."""
    filepath = os.path.join(get_exercises_dir(), f"{ex_id}.json")
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False


def execute_sandboxed(code, func_name, args, timeout_seconds=5):
    security_issues = analyze_security(code)
    if security_issues:
        return {"success": False, "error": "Código contém instruções não permitidas"}
    
    sandbox_globals = {'__builtins__': SAFE_BUILTINS, '__name__': '__sandbox__'}
    
    try:
        start_time = time.time()
        exec(code, sandbox_globals)
        
        if func_name not in sandbox_globals:
            return {"success": False, "error": f"Função '{func_name}' não definida"}
        
        func = sandbox_globals[func_name]
        if isinstance(args, list):
            result = func(*args)
        else:
            result = func(args)
        
        elapsed = time.time() - start_time
        return {"success": True, "result": result, "time": elapsed}
        
    except Exception as e:
        return {"success": False, "error": str(e), "error_type": type(e).__name__}


def run_tests(code, exercise):
    func_name = exercise.get("function")
    tests = exercise.get("tests", [])
    results = []
    
    for i, test in enumerate(tests):
        test_input = test.get("input")
        expected = test.get("output")
        hint = test.get("hint", "")
        
        execution = execute_sandboxed(code, func_name, test_input)
        
        if execution["success"]:
            actual = execution["result"]
            passed = (actual == expected)
            
            # Gerar dicas inteligentes se falhou
            smart_hints = []
            if not passed:
                smart_hints = get_smart_hint(None, actual, expected)
            
            results.append({
                "test_number": i + 1, "input": test_input, "expected": expected,
                "actual": actual, "passed": passed, "time": execution.get("time", 0),
                "hint": hint, "smart_hints": smart_hints
            })
        else:
            smart_hints = get_smart_hint(execution.get("error", ""), None, expected)
            results.append({
                "test_number": i + 1, "input": test_input, "expected": expected,
                "actual": None, "passed": False, "error": execution.get("error"),
                "hint": hint, "smart_hints": smart_hints
            })
    
    return results


def evaluate_submission(ex_id, code):
    exercise = load_exercise(ex_id)
    static = full_static_analysis(code)
    test_results = run_tests(code, exercise)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for t in test_results if t.get("passed"))
    
    test_score = (passed_tests / total_tests * 80) if total_tests > 0 else 0
    security_penalty = len(static["security"]) * 20
    style_penalty = min(len(static["style"]), 5) * 2
    quality_penalty = min(len(static["quality"]), 3) * 2
    
    final_score = max(0, test_score + 20 - security_penalty - style_penalty - quality_penalty)
    
    return {
        "exercise_id": ex_id,
        "exercise_title": exercise.get("title"),
        "timestamp": datetime.now().isoformat(),
        "code": code,
        "static_analysis": static,
        "dynamic_analysis": {
            "tests": test_results,
            "summary": {"total": total_tests, "passed": passed_tests, "failed": total_tests - passed_tests}
        },
        "evaluation": {
            "test_score": round(test_score, 1),
            "security_penalty": security_penalty,
            "style_penalty": style_penalty,
            "quality_penalty": quality_penalty,
            "final_score": round(final_score, 1),
            "status": "approved" if final_score >= 50 else "failed"
        }
    }


# =============================================================================
# GERAÇÃO DE PDF
# =============================================================================

def generate_pdf_report(report, username):
    """Gera relatório PDF."""
    try:
        from fpdf import FPDF
    except ImportError:
        return None
    
    pdf = FPDF()
    pdf.add_page()
    
    # Título
    pdf.set_font('Arial', 'B', 20)
    pdf.cell(0, 15, 'Relatório de Avaliação', ln=True, align='C')
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f'Avaliador Automático Python', ln=True, align='C')
    pdf.ln(10)
    
    # Info do aluno
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Informações', ln=True)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, f'Aluno: {username}', ln=True)
    pdf.cell(0, 8, f'Exercício: {report.get("exercise_title", report.get("exercise_id"))}', ln=True)
    pdf.cell(0, 8, f'Data: {report.get("timestamp", "")[:19].replace("T", " ")}', ln=True)
    pdf.ln(5)
    
    # Resultado
    evaluation = report.get('evaluation', {})
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Resultado', ln=True)
    pdf.set_font('Arial', 'B', 16)
    status_text = 'APROVADO' if evaluation.get('status') == 'approved' else 'REPROVADO'
    pdf.cell(0, 10, f'Nota Final: {evaluation.get("final_score", 0)}/100 - {status_text}', ln=True)
    pdf.ln(5)
    
    # Testes
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Resultados dos Testes', ln=True)
    pdf.set_font('Arial', '', 10)
    
    summary = report.get('dynamic_analysis', {}).get('summary', {})
    pdf.cell(0, 8, f'Testes: {summary.get("passed", 0)}/{summary.get("total", 0)} corretos', ln=True)
    
    for test in report.get('dynamic_analysis', {}).get('tests', []):
        status = '[OK]' if test.get('passed') else '[ERRO]'
        pdf.cell(0, 6, f'  {status} Teste {test.get("test_number")}: input={test.get("input")} esperado={test.get("expected")} obtido={test.get("actual")}', ln=True)
    
    pdf.ln(5)
    
    # Análise Estática
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Análise Estática', ln=True)
    pdf.set_font('Arial', '', 10)
    
    static = report.get('static_analysis', {})
    complexity = static.get('complexity', {})
    
    pdf.cell(0, 6, f'Linhas de código: {complexity.get("lines_of_code", 0)}', ln=True)
    pdf.cell(0, 6, f'Funções: {complexity.get("num_functions", 0)}', ln=True)
    pdf.cell(0, 6, f'Complexidade: {complexity.get("complexity_score", 0)}', ln=True)
    
    if static.get('security'):
        pdf.cell(0, 6, f'Problemas de segurança: {len(static.get("security", []))}', ln=True)
    if static.get('style'):
        pdf.cell(0, 6, f'Problemas de estilo: {len(static.get("style", []))}', ln=True)
    
    pdf.ln(10)
    
    # Código submetido
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Código Submetido', ln=True)
    pdf.set_font('Courier', '', 9)
    
    code = report.get('code', '')
    for line in code.split('\n')[:30]:
        pdf.cell(0, 5, line[:80], ln=True)
    
    if len(code.split('\n')) > 30:
        pdf.cell(0, 5, '... (código truncado)', ln=True)
    
    return bytes(pdf.output())


def get_pdf_download_link(pdf_bytes, filename):
    """Gera link de download para PDF."""
    b64 = base64.b64encode(pdf_bytes).decode()
    return f'<a href="data:application/pdf;base64,{b64}" download="{filename}">📄 Descarregar Relatório PDF</a>'


# =============================================================================
# GESTÃO DE SESSÃO
# =============================================================================

def init_session():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'last_report' not in st.session_state:
        st.session_state.last_report = None


def logout():
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.last_report = None


# =============================================================================
# COMPONENTE: EDITOR DE CÓDIGO
# =============================================================================

def code_editor(default_code, key="code"):
    """Editor de código com syntax highlighting básico."""
    # Tentar usar streamlit-ace se disponível
    try:
        from streamlit_ace import st_ace
        code = st_ace(
            value=default_code,
            language='python',
            theme='monokai',
            height=300,
            key=key,
            font_size=14,
            tab_size=4,
            show_gutter=True,
            show_print_margin=False,
            wrap=True,
            auto_update=True
        )
        return code
    except ImportError:
        # Fallback para textarea normal com estilo melhorado
        st.markdown("""
        <style>
        .stTextArea textarea {
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace !important;
            font-size: 14px !important;
            background-color: #1e1e1e !important;
            color: #d4d4d4 !important;
            border-radius: 8px !important;
        }
        </style>
        """, unsafe_allow_html=True)
        return st.text_area("💻 Código:", value=default_code, height=300, key=key)


# =============================================================================
# PÁGINAS
# =============================================================================

def page_login():
    st.markdown('<div class="main-header">🐍 Avaliador Automático Python v3.0</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 👤 Entrar na conta")
        
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Registar"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Entrar", use_container_width=True)
                
                if submit:
                    if username and password:
                        user = db_login(username, password)
                        if user:
                            st.session_state.logged_in = True
                            st.session_state.user = user
                            st.success(f"Bem-vindo, {username}!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Username ou password incorretos")
                    else:
                        st.warning("Preenche todos os campos")
        
        with tab2:
            with st.form("register_form"):
                new_username = st.text_input("Username", key="reg_user")
                new_password = st.text_input("Password", type="password", key="reg_pass")
                confirm_password = st.text_input("Confirmar Password", type="password")
                submit_reg = st.form_submit_button("Criar Conta", use_container_width=True)
                
                if submit_reg:
                    if new_username and new_password and confirm_password:
                        if new_password != confirm_password:
                            st.error("Passwords não coincidem")
                        elif len(new_password) < 4:
                            st.error("Password deve ter pelo menos 4 caracteres")
                        else:
                            result, msg = db_register(new_username, new_password)
                            if result:
                                st.success(msg)
                            else:
                                st.error(msg)
                    else:
                        st.warning("Preenche todos os campos")
        
        st.markdown("---")
        st.caption("🔐 Contas de teste: `professor`/`admin123` | `aluno1`/`teste123`")


def page_main():
    user = st.session_state.user
    is_professor = user.get('role') == 'professor'
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👤 {user.get('username')}")
        
        if is_professor:
            st.markdown('<span class="professor-badge">👨‍🏫 Professor</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="user-badge">🎓 Aluno</span>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        stats = db_get_user_stats(user.get('username'))
        st.markdown("### 📊 Estatísticas")
        
        col1, col2 = st.columns(2)
        col1.metric("Submissões", stats['total'])
        col2.metric("Aprovadas", stats['approved'])
        
        col1, col2 = st.columns(2)
        col1.metric("Média", f"{stats['average']}")
        col2.metric("Exercícios", stats['exercises_done'])
        
        st.markdown("---")
        
        if st.button("🚪 Sair", use_container_width=True):
            logout()
            st.rerun()
    
    # Header
    st.markdown('<div class="main-header">🐍 Avaliador Automático Python v3.0</div>', unsafe_allow_html=True)
    
    # Tabs
    if is_professor:
        tabs = st.tabs(["📝 Exercícios", "🚀 Avaliar", "📜 Histórico", "👥 Alunos", "📊 Submissões", "⚙️ Gerir Exercícios"])
    else:
        tabs = st.tabs(["📝 Exercícios", "🚀 Avaliar", "📜 Histórico"])
    
    # TAB 1 - EXERCÍCIOS
    with tabs[0]:
        st.header("📚 Exercícios Disponíveis")
        exercises = list_exercises()
        
        col1, col2 = st.columns([3, 1])
        with col1:
            search = st.text_input("🔍 Pesquisar...", placeholder="Nome do exercício")
        with col2:
            st.metric("Total", len(exercises))
        
        if search:
            exercises = [ex for ex in exercises if search.lower() in ex.get('title', '').lower() or search.lower() in ex['id'].lower()]
        
        for ex in exercises:
            with st.expander(f"📌 {ex.get('title', ex['id'])} (`{ex['id']}`)"):
                st.markdown(f"**Função:** `{ex.get('function', 'N/A')}()`")
                st.markdown(f"**Descrição:** {ex.get('description', 'Sem descrição')}")
                
                tests = ex.get('tests', [])
                if tests:
                    st.markdown(f"**Exemplos ({len(tests)} testes):**")
                    for test in tests[:3]:
                        st.code(f"{ex.get('function')}({test['input']}) → {test['output']}", language=None)
    
    # TAB 2 - AVALIAR
    with tabs[1]:
        st.header("🚀 Submeter Código")
        exercises = list_exercises()
        
        if exercises:
            exercise_options = {f"{ex.get('title', ex['id'])}": ex['id'] for ex in exercises}
            selected_name = st.selectbox("📋 Exercício:", list(exercise_options.keys()))
            selected_id = exercise_options[selected_name]
            
            exercise = load_exercise(selected_id)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info(f"**Função:** `{exercise.get('function')}()`\n\n{exercise.get('description', '')}")
            with col2:
                st.metric("Testes", len(exercise.get('tests', [])))
            
            default_code = f"""def {exercise.get('function', 'funcao')}(n):
    # Escreve o teu código aqui
    pass
"""
            
            code = code_editor(default_code, key="main_editor")
            
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                evaluate_btn = st.button("🚀 Avaliar", type="primary", use_container_width=True)
            with col2:
                if st.session_state.last_report:
                    pdf_btn = st.button("📄 Exportar PDF", use_container_width=True)
                else:
                    pdf_btn = False
            
            if evaluate_btn and code.strip():
                with st.spinner("A avaliar..."):
                    report = evaluate_submission(selected_id, code)
                    st.session_state.last_report = report
                
                db_save_submission(
                    user.get('id'), user.get('username'), selected_id,
                    exercise.get('title'), code, report['evaluation']['final_score'],
                    report['dynamic_analysis']['summary']['passed'],
                    report['dynamic_analysis']['summary']['total'],
                    report['evaluation']['status']
                )
                
                # RESULTADO
                st.markdown("---")
                st.header("📊 Resultado")
                
                evaluation = report['evaluation']
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    score_class = "score-approved" if evaluation['status'] == 'approved' else "score-failed"
                    st.markdown(f"<div class='{score_class}'>{evaluation['final_score']}/100</div>", unsafe_allow_html=True)
                with col2:
                    st.metric("Testes", f"{report['dynamic_analysis']['summary']['passed']}/{report['dynamic_analysis']['summary']['total']}")
                with col3:
                    if evaluation['status'] == 'approved':
                        st.success("✅ APROVADO")
                    else:
                        st.error("❌ REPROVADO")
                
                # Testes com dicas inteligentes
                st.subheader("🧪 Testes")
                for test in report['dynamic_analysis']['tests']:
                    if test['passed']:
                        st.success(f"✅ Teste {test['test_number']}: `{exercise.get('function')}({test['input']})` → `{test['actual']}`")
                    else:
                        st.error(f"❌ Teste {test['test_number']}: Esperado `{test['expected']}`, obteve `{test['actual']}`")
                        
                        # Dicas inteligentes
                        if test.get('smart_hints'):
                            for hint in test['smart_hints']:
                                st.markdown(f'<div class="hint-box">{hint}</div>', unsafe_allow_html=True)
                        elif test.get('hint'):
                            st.info(f"💡 {test['hint']}")
                        
                        if test.get('error'):
                            with st.expander("Ver erro técnico"):
                                st.code(test['error'])
                
                # Análise estática
                st.subheader("🔍 Análise do Código")
                static = report['static_analysis']
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if static['security']:
                        st.error(f"🔒 {len(static['security'])} problema(s) de segurança")
                    else:
                        st.success("🔒 Segurança OK")
                with col2:
                    if static['style']:
                        st.warning(f"📝 {len(static['style'])} aviso(s) de estilo")
                    else:
                        st.success("📝 Estilo OK")
                with col3:
                    complexity = static['complexity']
                    st.info(f"📊 {complexity['lines_of_code']} linhas")
                
                # Detalhes
                with st.expander("📋 Ver detalhes da análise"):
                    if static['security']:
                        st.markdown("**Problemas de Segurança:**")
                        for issue in static['security']:
                            st.markdown(f'<div class="security-alert">{issue["message"]}</div>', unsafe_allow_html=True)
                    
                    if static['style']:
                        st.markdown("**Avisos de Estilo:**")
                        for issue in static['style'][:5]:
                            st.markdown(f'<div class="style-warning">{issue["message"]}</div>', unsafe_allow_html=True)
                    
                    if static['quality']:
                        st.markdown("**Sugestões de Qualidade:**")
                        for issue in static['quality']:
                            st.info(issue["message"])
                    
                    st.markdown("**Métricas:**")
                    metrics = static['complexity']
                    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
                    mcol1.metric("Linhas", metrics['lines_of_code'])
                    mcol2.metric("Funções", metrics['num_functions'])
                    mcol3.metric("Loops", metrics['num_loops'])
                    mcol4.metric("Complexidade", metrics['complexity_score'])
            
            # Exportar PDF
            if pdf_btn and st.session_state.last_report:
                pdf_bytes = generate_pdf_report(st.session_state.last_report, user.get('username'))
                if pdf_bytes:
                    st.markdown(get_pdf_download_link(pdf_bytes, f"relatorio_{selected_id}.pdf"), unsafe_allow_html=True)
                else:
                    st.warning("Instale fpdf2 para exportar PDF: `pip install fpdf2`")
    
    # TAB 3 - HISTÓRICO
    with tabs[2]:
        st.header("📜 Histórico")
        submissions = db_get_user_submissions(user.get('username'))
        
        if not submissions:
            st.info("Ainda não tens submissões.")
        else:
            for sub in submissions[:20]:
                status_icon = "✅" if sub.get('status') == 'approved' else "❌"
                with st.expander(f"{status_icon} {sub.get('exercise_title', sub.get('exercise_id'))} - {sub.get('score')}/100 - {str(sub.get('created_at', ''))[:10]}"):
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Nota", f"{sub.get('score')}/100")
                    col2.metric("Testes", f"{sub.get('tests_passed')}/{sub.get('tests_total')}")
                    col3.metric("Status", "Aprovado" if sub.get('status') == 'approved' else "Reprovado")
                    st.code(sub.get('code', ''), language='python')
    
    # TABS PROFESSOR
    if is_professor:
        # TAB 4 - ALUNOS
        with tabs[3]:
            st.header("👥 Alunos")
            users = db_get_all_users()
            
            st.metric("Total de Utilizadores", len(users))
            
            for u in users:
                role_badge = "👨‍🏫" if u.get('role') == 'professor' else "🎓"
                user_stats = db_get_user_stats(u.get('username'))
                
                with st.expander(f"{role_badge} {u.get('username')} ({u.get('role')})"):
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Submissões", user_stats['total'])
                    col2.metric("Aprovadas", user_stats['approved'])
                    col3.metric("Média", user_stats['average'])
                    col4.metric("Exercícios", user_stats['exercises_done'])
        
        # TAB 5 - SUBMISSÕES
        with tabs[4]:
            st.header("📊 Todas as Submissões")
            all_subs = db_get_all_submissions()
            
            col1, col2 = st.columns(2)
            with col1:
                filter_user = st.text_input("Filtrar por aluno")
            with col2:
                filter_ex = st.text_input("Filtrar por exercício")
            
            filtered = all_subs
            if filter_user:
                filtered = [s for s in filtered if filter_user.lower() in s.get('username', '').lower()]
            if filter_ex:
                filtered = [s for s in filtered if filter_ex.lower() in s.get('exercise_id', '').lower()]
            
            st.caption(f"{len(filtered)} submissões")
            
            for sub in filtered[:30]:
                status_icon = "✅" if sub.get('status') == 'approved' else "❌"
                with st.expander(f"{status_icon} {sub.get('username')} - {sub.get('exercise_title')} - {sub.get('score')}/100"):
                    st.code(sub.get('code', ''), language='python')
        
        # TAB 6 - GERIR EXERCÍCIOS
        with tabs[5]:
            st.header("⚙️ Gerir Exercícios")
            
            st.subheader("➕ Adicionar Novo Exercício")
            
            with st.form("new_exercise"):
                new_id = st.text_input("ID (sem espaços)", placeholder="ex: soma_lista")
                new_title = st.text_input("Título", placeholder="Soma de Lista")
                new_desc = st.text_area("Descrição", placeholder="Crie uma função que...")
                new_func = st.text_input("Nome da Função", placeholder="soma_lista")
                new_tests = st.text_area("Testes (JSON)", placeholder='[{"input": [1,2], "output": 3}]', height=100)
                
                if st.form_submit_button("💾 Guardar Exercício"):
                    if new_id and new_title and new_func and new_tests:
                        try:
                            tests = json.loads(new_tests)
                            exercise_data = {
                                "title": new_title,
                                "description": new_desc,
                                "function": new_func,
                                "tests": tests
                            }
                            save_exercise(new_id, exercise_data)
                            st.success(f"Exercício '{new_title}' criado!")
                            st.rerun()
                        except json.JSONDecodeError:
                            st.error("Testes JSON inválido")
                    else:
                        st.warning("Preenche todos os campos obrigatórios")
            
            st.markdown("---")
            st.subheader("📋 Exercícios Existentes")
            
            exercises = list_exercises()
            for ex in exercises:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{ex.get('title')}** (`{ex['id']}`)")
                with col2:
                    if st.button("🗑️", key=f"del_{ex['id']}"):
                        delete_exercise(ex['id'])
                        st.success(f"Exercício '{ex['id']}' apagado!")
                        st.rerun()


# =============================================================================
# MAIN
# =============================================================================

def main():
    init_session()
    
    if st.session_state.logged_in:
        page_main()
    else:
        page_login()


if __name__ == "__main__":
    main()
