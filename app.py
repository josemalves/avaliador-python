#!/usr/bin/env python3
"""
Avaliador Automático de Programas Python
Versão 2.0 - Com Sistema de Utilizadores (Supabase)
"""

import streamlit as st
import json
import os
import re
import time
from datetime import datetime
import requests

# =============================================================================
# CONFIGURAÇÃO SUPABASE
# =============================================================================

SUPABASE_URL = "https://jssnogllerzeezgeodxy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Impzc25vZ2xsZXJ6ZWV6Z2VvZHh5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjUyMzU4NTksImV4cCI6MjA4MDgxMTg1OX0.6DAaTeFLkLNDOeZsjS93ee53z5wvncHKAFlY046Cw6s"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# =============================================================================
# FUNÇÕES SUPABASE
# =============================================================================

def db_login(username, password):
    """Verifica login do utilizador."""
    url = f"{SUPABASE_URL}/rest/v1/users?username=eq.{username}&password=eq.{password}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        users = response.json()
        if users:
            return users[0]
    return None


def db_register(username, password, role="aluno"):
    """Regista novo utilizador."""
    # Verificar se já existe
    url = f"{SUPABASE_URL}/rest/v1/users?username=eq.{username}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200 and response.json():
        return None, "Username já existe"
    
    # Criar utilizador
    url = f"{SUPABASE_URL}/rest/v1/users"
    data = {"username": username, "password": password, "role": role}
    response = requests.post(url, headers=HEADERS, json=data)
    
    if response.status_code == 201:
        return True, "Conta criada com sucesso!"
    return None, "Erro ao criar conta"


def db_save_submission(user_id, username, exercise_id, exercise_title, code, score, tests_passed, tests_total, status):
    """Guarda submissão na base de dados."""
    url = f"{SUPABASE_URL}/rest/v1/submissions"
    data = {
        "user_id": user_id,
        "username": username,
        "exercise_id": exercise_id,
        "exercise_title": exercise_title,
        "code": code,
        "score": score,
        "tests_passed": tests_passed,
        "tests_total": tests_total,
        "status": status
    }
    response = requests.post(url, headers=HEADERS, json=data)
    return response.status_code == 201


def db_get_user_submissions(username):
    """Obtém submissões de um utilizador."""
    url = f"{SUPABASE_URL}/rest/v1/submissions?username=eq.{username}&order=created_at.desc"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    return []


def db_get_all_submissions():
    """Obtém todas as submissões (para professor)."""
    url = f"{SUPABASE_URL}/rest/v1/submissions?order=created_at.desc"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    return []


def db_get_all_users():
    """Obtém todos os utilizadores (para professor)."""
    url = f"{SUPABASE_URL}/rest/v1/users?order=created_at.desc"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    return []


def db_get_user_stats(username):
    """Calcula estatísticas do utilizador."""
    submissions = db_get_user_submissions(username)
    if not submissions:
        return {"total": 0, "approved": 0, "average": 0, "exercises_done": 0}
    
    total = len(submissions)
    approved = sum(1 for s in submissions if s.get('status') == 'approved')
    scores = [s.get('score', 0) for s in submissions if s.get('score') is not None]
    average = sum(scores) / len(scores) if scores else 0
    exercises_done = len(set(s.get('exercise_id') for s in submissions))
    
    return {
        "total": total,
        "approved": approved,
        "average": round(average, 1),
        "exercises_done": exercises_done
    }


# =============================================================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================================================

st.set_page_config(
    page_title="Avaliador Automático Python",
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
        background: linear-gradient(90deg, #1e3a8a, #3b82f6);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .user-badge {
        background: linear-gradient(90deg, #10b981, #059669);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    .professor-badge {
        background: linear-gradient(90deg, #8b5cf6, #7c3aed);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    .score-approved {
        font-size: 2rem;
        color: #10b981;
        font-weight: bold;
    }
    .score-failed {
        font-size: 2rem;
        color: #ef4444;
        font-weight: bold;
    }
    .stat-card {
        background: #f0f9ff;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        border: 1px solid #bae6fd;
    }
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background: #f8fafc;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# MOTOR DE AVALIAÇÃO
# =============================================================================

FORBIDDEN_KEYWORDS = [
    r'\bimport\s+os\b', r'\bimport\s+sys\b', r'\bimport\s+subprocess\b',
    r'\bimport\s+socket\b', r'\bfrom\s+os\b', r'\bopen\s*\(',
    r'\beval\s*\(', r'\bexec\s*\(', r'\b__import__\s*\(',
    r'\bcompile\s*\(', r'\bglobals\s*\(', r'\blocals\s*\(',
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
            with open(filepath, 'r', encoding='utf-8') as f:
                exercise = json.load(f)
                exercise['id'] = ex_id
                exercise_list.append(exercise)
    return sorted(exercise_list, key=lambda x: x.get('title', x['id']))


def load_exercise(ex_id):
    filepath = os.path.join(get_exercises_dir(), f"{ex_id}.json")
    with open(filepath, 'r', encoding='utf-8') as f:
        exercise = json.load(f)
        exercise['id'] = ex_id
        return exercise


def analyze_security(code):
    issues = []
    for pattern in FORBIDDEN_KEYWORDS:
        matches = re.findall(pattern, code)
        if matches:
            issues.append({"type": "security", "message": f"Código potencialmente perigoso: {matches[0]}"})
    return issues


def analyze_style(code):
    issues = []
    lines = code.split('\n')
    for i, line in enumerate(lines, 1):
        if len(line) > 100:
            issues.append({"line": i, "message": f"Linha {i} muito longa ({len(line)} caracteres)"})
        if '\t' in line:
            issues.append({"line": i, "message": f"Linha {i} usa tabs em vez de espaços"})
    return issues[:10]


def analyze_complexity(code):
    return {
        "lines_of_code": len([l for l in code.split('\n') if l.strip() and not l.strip().startswith('#')]),
        "num_functions": len(re.findall(r'\bdef\s+\w+', code)),
        "num_classes": len(re.findall(r'\bclass\s+\w+', code)),
        "num_loops": len(re.findall(r'\b(for|while)\b', code)),
        "num_conditionals": len(re.findall(r'\b(if|elif)\b', code)),
    }


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
            results.append({
                "test_number": i + 1, "input": test_input, "expected": expected,
                "actual": actual, "passed": passed, "time": execution.get("time", 0),
                "hint": hint if not passed else ""
            })
        else:
            results.append({
                "test_number": i + 1, "input": test_input, "expected": expected,
                "actual": None, "passed": False, "error": execution.get("error"), "hint": hint
            })
    
    return results


def evaluate_submission(ex_id, code):
    exercise = load_exercise(ex_id)
    security_issues = analyze_security(code)
    style_issues = analyze_style(code)
    complexity = analyze_complexity(code)
    test_results = run_tests(code, exercise)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for t in test_results if t.get("passed"))
    
    test_score = (passed_tests / total_tests * 80) if total_tests > 0 else 0
    security_penalty = len(security_issues) * 10
    style_penalty = min(len(style_issues), 5) * 2
    final_score = max(0, test_score + 20 - security_penalty - style_penalty)
    
    return {
        "exercise_id": ex_id,
        "exercise_title": exercise.get("title"),
        "timestamp": datetime.now().isoformat(),
        "static_analysis": {"security": security_issues, "style": style_issues, "complexity": complexity},
        "dynamic_analysis": {
            "tests": test_results,
            "summary": {"total": total_tests, "passed": passed_tests, "failed": total_tests - passed_tests}
        },
        "evaluation": {
            "test_score": round(test_score, 1),
            "security_penalty": security_penalty,
            "style_penalty": style_penalty,
            "final_score": round(final_score, 1),
            "status": "approved" if final_score >= 50 else "failed"
        }
    }


# =============================================================================
# GESTÃO DE SESSÃO
# =============================================================================

def init_session():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'page' not in st.session_state:
        st.session_state.page = 'login'


def logout():
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.page = 'login'


# =============================================================================
# PÁGINAS
# =============================================================================

def page_login():
    st.markdown('<div class="main-header">🐍 Avaliador Automático Python</div>', unsafe_allow_html=True)
    
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
                                st.success(msg + " Podes fazer login agora.")
                            else:
                                st.error(msg)
                    else:
                        st.warning("Preenche todos os campos")
        
        st.markdown("---")
        st.caption("Contas de teste: professor/admin123 | aluno1/teste123")


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
        
        # Estatísticas pessoais
        stats = db_get_user_stats(user.get('username'))
        st.markdown("### 📊 As minhas estatísticas")
        st.metric("Submissões", stats['total'])
        st.metric("Aprovadas", stats['approved'])
        st.metric("Média", f"{stats['average']}/100")
        st.metric("Exercícios Feitos", stats['exercises_done'])
        
        st.markdown("---")
        
        if st.button("🚪 Sair", use_container_width=True):
            logout()
            st.rerun()
    
    # Header
    st.markdown('<div class="main-header">🐍 Avaliador Automático Python</div>', unsafe_allow_html=True)
    
    # Tabs - diferentes para professor e aluno
    if is_professor:
        tabs = st.tabs(["📝 Exercícios", "🚀 Avaliar", "📜 Meu Histórico", "👥 Alunos", "📊 Todas Submissões"])
    else:
        tabs = st.tabs(["📝 Exercícios", "🚀 Avaliar", "📜 Meu Histórico"])
    
    # TAB 1 - EXERCÍCIOS
    with tabs[0]:
        st.header("📚 Exercícios Disponíveis")
        exercises = list_exercises()
        
        if not exercises:
            st.warning("Nenhum exercício encontrado.")
        else:
            search = st.text_input("🔍 Pesquisar exercício...")
            
            if search:
                exercises = [ex for ex in exercises if search.lower() in ex.get('title', '').lower() or search.lower() in ex['id'].lower()]
            
            for ex in exercises:
                with st.expander(f"📌 {ex.get('title', ex['id'])}"):
                    st.markdown(f"**ID:** `{ex['id']}`")
                    st.markdown(f"**Função:** `{ex.get('function', 'N/A')}()`")
                    st.markdown(f"**Descrição:** {ex.get('description', 'Sem descrição')}")
                    
                    tests = ex.get('tests', [])
                    if tests:
                        st.markdown("**Exemplos:**")
                        for test in tests[:3]:
                            st.code(f"{ex.get('function')}({test['input']}) → {test['output']}", language=None)
                        if len(tests) > 3:
                            st.caption(f"... e mais {len(tests) - 3} testes")
    
    # TAB 2 - AVALIAR
    with tabs[1]:
        st.header("🚀 Submeter Código para Avaliação")
        exercises = list_exercises()
        
        if exercises:
            exercise_options = {f"{ex.get('title', ex['id'])}": ex['id'] for ex in exercises}
            selected_name = st.selectbox("📋 Escolhe um exercício:", list(exercise_options.keys()))
            selected_id = exercise_options[selected_name]
            
            exercise = load_exercise(selected_id)
            
            st.info(f"**Função:** `{exercise.get('function')}()`\n\n{exercise.get('description', '')}")
            
            default_code = f"""def {exercise.get('function', 'funcao')}(n):
    # Escreve o teu código aqui
    pass
"""
            
            code = st.text_area("💻 Escreve o teu código:", value=default_code, height=300)
            
            if st.button("🚀 Avaliar", type="primary", use_container_width=True):
                if code.strip():
                    with st.spinner("A avaliar..."):
                        report = evaluate_submission(selected_id, code)
                    
                    # Guardar na base de dados
                    db_save_submission(
                        user_id=user.get('id'),
                        username=user.get('username'),
                        exercise_id=selected_id,
                        exercise_title=exercise.get('title'),
                        code=code,
                        score=report['evaluation']['final_score'],
                        tests_passed=report['dynamic_analysis']['summary']['passed'],
                        tests_total=report['dynamic_analysis']['summary']['total'],
                        status=report['evaluation']['status']
                    )
                    
                    # Mostrar resultado
                    st.markdown("---")
                    evaluation = report['evaluation']
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        score_class = "score-approved" if evaluation['status'] == 'approved' else "score-failed"
                        st.markdown(f"<div class='{score_class}'>{evaluation['final_score']}/100</div>", unsafe_allow_html=True)
                        st.caption("Nota Final")
                    with col2:
                        st.metric("Testes", f"{report['dynamic_analysis']['summary']['passed']}/{report['dynamic_analysis']['summary']['total']}")
                    with col3:
                        if evaluation['status'] == 'approved':
                            st.success("✅ APROVADO")
                        else:
                            st.error("❌ REPROVADO")
                    
                    # Detalhes
                    st.subheader("🧪 Resultados")
                    for test in report['dynamic_analysis']['tests']:
                        if test['passed']:
                            st.success(f"✅ Teste {test['test_number']}: `{exercise.get('function')}({test['input']})` → `{test['actual']}`")
                        else:
                            st.error(f"❌ Teste {test['test_number']}: Esperado `{test['expected']}`, obteve `{test['actual']}`")
                            if test.get('hint'):
                                st.info(f"💡 {test['hint']}")
    
    # TAB 3 - HISTÓRICO
    with tabs[2]:
        st.header("📜 O Meu Histórico de Submissões")
        
        submissions = db_get_user_submissions(user.get('username'))
        
        if not submissions:
            st.info("Ainda não tens submissões. Vai à tab 'Avaliar' para começar!")
        else:
            for sub in submissions[:20]:
                status_icon = "✅" if sub.get('status') == 'approved' else "❌"
                with st.expander(f"{status_icon} {sub.get('exercise_title', sub.get('exercise_id'))} - {sub.get('score')}/100"):
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Nota", f"{sub.get('score')}/100")
                    col2.metric("Testes", f"{sub.get('tests_passed')}/{sub.get('tests_total')}")
                    col3.metric("Data", sub.get('created_at', '')[:10])
                    
                    st.code(sub.get('code', ''), language='python')
    
    # TABS SÓ PARA PROFESSOR
    if is_professor:
        # TAB 4 - ALUNOS
        with tabs[3]:
            st.header("👥 Gestão de Alunos")
            
            users = db_get_all_users()
            
            st.metric("Total de Utilizadores", len(users))
            
            st.markdown("---")
            
            for u in users:
                role_badge = "👨‍🏫" if u.get('role') == 'professor' else "🎓"
                user_stats = db_get_user_stats(u.get('username'))
                
                with st.expander(f"{role_badge} {u.get('username')} ({u.get('role')})"):
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Submissões", user_stats['total'])
                    col2.metric("Aprovadas", user_stats['approved'])
                    col3.metric("Média", f"{user_stats['average']}")
                    col4.metric("Exercícios", user_stats['exercises_done'])
        
        # TAB 5 - TODAS SUBMISSÕES
        with tabs[4]:
            st.header("📊 Todas as Submissões")
            
            all_subs = db_get_all_submissions()
            
            if not all_subs:
                st.info("Nenhuma submissão ainda.")
            else:
                # Filtros
                col1, col2 = st.columns(2)
                with col1:
                    filter_user = st.text_input("Filtrar por utilizador")
                with col2:
                    filter_exercise = st.text_input("Filtrar por exercício")
                
                filtered = all_subs
                if filter_user:
                    filtered = [s for s in filtered if filter_user.lower() in s.get('username', '').lower()]
                if filter_exercise:
                    filtered = [s for s in filtered if filter_exercise.lower() in s.get('exercise_id', '').lower()]
                
                st.markdown(f"**{len(filtered)} submissões encontradas**")
                
                for sub in filtered[:50]:
                    status_icon = "✅" if sub.get('status') == 'approved' else "❌"
                    with st.expander(f"{status_icon} {sub.get('username')} - {sub.get('exercise_title')} - {sub.get('score')}/100"):
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Aluno", sub.get('username'))
                        col2.metric("Nota", f"{sub.get('score')}/100")
                        col3.metric("Testes", f"{sub.get('tests_passed')}/{sub.get('tests_total')}")
                        col4.metric("Data", sub.get('created_at', '')[:10])
                        
                        st.code(sub.get('code', ''), language='python')


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
