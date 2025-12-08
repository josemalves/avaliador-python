#!/usr/bin/env python3
"""
Avaliador Automático de Programas Python
Versão Streamlit Cloud - Tudo numa única aplicação
"""

import streamlit as st
import json
import os
import re
import time
from datetime import datetime

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
    .exercise-card {
        background-color: #f8fafc;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #3b82f6;
        margin: 0.5rem 0;
    }
    .stSuccess, .stError {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# MOTOR DE AVALIAÇÃO (INTEGRADO)
# =============================================================================

# Palavras-chave proibidas (segurança)
FORBIDDEN_KEYWORDS = [
    r'\bimport\s+os\b',
    r'\bimport\s+sys\b', 
    r'\bimport\s+subprocess\b',
    r'\bimport\s+socket\b',
    r'\bfrom\s+os\b',
    r'\bopen\s*\(',
    r'\beval\s*\(',
    r'\bexec\s*\(',
    r'\b__import__\s*\(',
    r'\bcompile\s*\(',
    r'\bglobals\s*\(',
    r'\blocals\s*\(',
]

# Builtins seguros
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
    """Retorna o caminho para a pasta de exercícios."""
    return os.path.join(os.path.dirname(__file__), 'exercises')


def list_exercises():
    """Lista todos os exercícios disponíveis."""
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
    """Carrega um exercício pelo ID."""
    filepath = os.path.join(get_exercises_dir(), f"{ex_id}.json")
    with open(filepath, 'r', encoding='utf-8') as f:
        exercise = json.load(f)
        exercise['id'] = ex_id
        return exercise


def analyze_security(code):
    """Analisa código por problemas de segurança."""
    issues = []
    for pattern in FORBIDDEN_KEYWORDS:
        matches = re.findall(pattern, code)
        if matches:
            issues.append({
                "type": "security",
                "message": f"Código potencialmente perigoso: {matches[0]}"
            })
    return issues


def analyze_style(code):
    """Análise básica de estilo."""
    issues = []
    lines = code.split('\n')
    
    for i, line in enumerate(lines, 1):
        if len(line) > 100:
            issues.append({"line": i, "message": f"Linha {i} muito longa ({len(line)} caracteres)"})
        if '\t' in line:
            issues.append({"line": i, "message": f"Linha {i} usa tabs em vez de espaços"})
    
    return issues[:10]  # Limitar a 10 issues


def analyze_complexity(code):
    """Métricas de complexidade."""
    return {
        "lines_of_code": len([l for l in code.split('\n') if l.strip() and not l.strip().startswith('#')]),
        "num_functions": len(re.findall(r'\bdef\s+\w+', code)),
        "num_classes": len(re.findall(r'\bclass\s+\w+', code)),
        "num_loops": len(re.findall(r'\b(for|while)\b', code)),
        "num_conditionals": len(re.findall(r'\b(if|elif)\b', code)),
    }


def execute_sandboxed(code, func_name, args, timeout_seconds=5):
    """Executa código em sandbox seguro."""
    # Verificar segurança
    security_issues = analyze_security(code)
    if security_issues:
        return {"success": False, "error": "Código contém instruções não permitidas"}
    
    # Namespace isolado
    sandbox_globals = {
        '__builtins__': SAFE_BUILTINS,
        '__name__': '__sandbox__',
    }
    
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
    """Executa os testes do exercício."""
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
                "test_number": i + 1,
                "input": test_input,
                "expected": expected,
                "actual": actual,
                "passed": passed,
                "time": execution.get("time", 0),
                "hint": hint if not passed else ""
            })
        else:
            results.append({
                "test_number": i + 1,
                "input": test_input,
                "expected": expected,
                "actual": None,
                "passed": False,
                "error": execution.get("error"),
                "hint": hint
            })
    
    return results


def evaluate_submission(ex_id, code):
    """Avalia uma submissão completa."""
    exercise = load_exercise(ex_id)
    
    # Análise estática
    security_issues = analyze_security(code)
    style_issues = analyze_style(code)
    complexity = analyze_complexity(code)
    
    # Testes
    test_results = run_tests(code, exercise)
    
    # Calcular nota
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
        "static_analysis": {
            "security": security_issues,
            "style": style_issues,
            "complexity": complexity
        },
        "dynamic_analysis": {
            "tests": test_results,
            "summary": {
                "total": total_tests,
                "passed": passed_tests,
                "failed": total_tests - passed_tests
            }
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
# INTERFACE STREAMLIT
# =============================================================================

def main():
    # Header
    st.markdown('<div class="main-header">🐍 Avaliador Automático de Python</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://www.python.org/static/community_logos/python-logo-generic.svg", width=200)
        st.markdown("---")
        st.markdown("### 📚 Sobre")
        st.info("""
        **Avaliador Automático** para exercícios de Python.
        
        ✅ Análise de segurança  
        ✅ Verificação de estilo  
        ✅ Testes automáticos  
        ✅ Feedback instantâneo
        """)
        
        st.markdown("---")
        st.markdown("### 📊 Estatísticas")
        exercises = list_exercises()
        st.metric("Total de Exercícios", len(exercises))
        
        st.markdown("---")
        st.markdown("### ℹ️ Informação")
        st.caption("Projeto TEI 2024/2025")
    
    # Tabs principais
    tab1, tab2, tab3 = st.tabs(["📝 Exercícios", "🚀 Avaliar Código", "❓ Ajuda"])
    
    # =========================================================================
    # TAB 1 - EXERCÍCIOS
    # =========================================================================
    with tab1:
        st.header("📚 Exercícios Disponíveis")
        
        exercises = list_exercises()
        
        if not exercises:
            st.warning("Nenhum exercício encontrado.")
        else:
            # Filtro por dificuldade
            col1, col2 = st.columns([3, 1])
            with col2:
                search = st.text_input("🔍 Pesquisar", placeholder="Nome do exercício...")
            
            # Filtrar exercícios
            if search:
                exercises = [ex for ex in exercises if search.lower() in ex.get('title', '').lower() or search.lower() in ex['id'].lower()]
            
            # Mostrar exercícios
            for ex in exercises:
                with st.expander(f"📌 {ex.get('title', ex['id'])}", expanded=False):
                    st.markdown(f"**ID:** `{ex['id']}`")
                    st.markdown(f"**Função:** `{ex.get('function', 'N/A')}()`")
                    st.markdown(f"**Descrição:** {ex.get('description', 'Sem descrição')}")
                    
                    # Exemplos de testes
                    tests = ex.get('tests', [])
                    if tests:
                        st.markdown("**Exemplos:**")
                        for test in tests[:3]:
                            st.code(f"{ex.get('function')}({test['input']}) → {test['output']}", language=None)
                        if len(tests) > 3:
                            st.caption(f"... e mais {len(tests) - 3} testes")
    
    # =========================================================================
    # TAB 2 - AVALIAR CÓDIGO
    # =========================================================================
    with tab2:
        st.header("🚀 Submeter Código para Avaliação")
        
        exercises = list_exercises()
        
        if not exercises:
            st.error("Nenhum exercício disponível.")
        else:
            # Seletor de exercício
            exercise_options = {f"{ex.get('title', ex['id'])}": ex['id'] for ex in exercises}
            selected_name = st.selectbox("📋 Escolhe um exercício:", list(exercise_options.keys()))
            selected_id = exercise_options[selected_name]
            
            # Mostrar info do exercício
            exercise = load_exercise(selected_id)
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.info(f"**Função:** `{exercise.get('function')}()`\n\n{exercise.get('description', '')}")
            with col2:
                st.metric("Nº de Testes", len(exercise.get('tests', [])))
            
            # Editor de código
            default_code = f"""def {exercise.get('function', 'funcao')}(n):
    # Escreve o teu código aqui
    pass
"""
            
            code = st.text_area(
                "💻 Escreve o teu código:",
                value=default_code,
                height=300,
                key="code_editor"
            )
            
            # Botões
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                evaluate_btn = st.button("🚀 Avaliar", type="primary", use_container_width=True)
            
            with col2:
                clear_btn = st.button("🗑️ Limpar", use_container_width=True)
            
            if clear_btn:
                st.rerun()
            
            # Avaliar
            if evaluate_btn:
                if not code.strip():
                    st.error("Por favor, escreve algum código!")
                else:
                    with st.spinner("A avaliar o teu código..."):
                        report = evaluate_submission(selected_id, code)
                    
                    # Mostrar resultado
                    st.markdown("---")
                    st.header("📊 Resultado da Avaliação")
                    
                    # Score principal
                    evaluation = report['evaluation']
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        score_class = "score-approved" if evaluation['status'] == 'approved' else "score-failed"
                        st.markdown(f"<div class='{score_class}'>{evaluation['final_score']}/100</div>", unsafe_allow_html=True)
                        st.caption("Nota Final")
                    
                    with col2:
                        st.metric("Testes Passados", f"{report['dynamic_analysis']['summary']['passed']}/{report['dynamic_analysis']['summary']['total']}")
                    
                    with col3:
                        if evaluation['status'] == 'approved':
                            st.success("✅ APROVADO")
                        else:
                            st.error("❌ REPROVADO")
                    
                    # Detalhes dos testes
                    st.subheader("🧪 Resultados dos Testes")
                    
                    for test in report['dynamic_analysis']['tests']:
                        if test['passed']:
                            st.success(f"✅ Teste {test['test_number']}: `{exercise.get('function')}({test['input']})` → `{test['actual']}`")
                        else:
                            st.error(f"❌ Teste {test['test_number']}: `{exercise.get('function')}({test['input']})` → Esperado `{test['expected']}`, obteve `{test['actual']}`")
                            if test.get('error'):
                                st.code(test['error'], language=None)
                            if test.get('hint'):
                                st.info(f"💡 Dica: {test['hint']}")
                    
                    # Análise estática
                    static = report['static_analysis']
                    
                    if static['security']:
                        st.subheader("🔒 Problemas de Segurança")
                        for issue in static['security']:
                            st.warning(f"⚠️ {issue['message']}")
                    
                    if static['style']:
                        with st.expander(f"📝 Problemas de Estilo ({len(static['style'])})"):
                            for issue in static['style']:
                                st.caption(f"• {issue['message']}")
                    
                    # Métricas
                    with st.expander("📊 Métricas do Código"):
                        metrics = static['complexity']
                        cols = st.columns(5)
                        cols[0].metric("Linhas", metrics['lines_of_code'])
                        cols[1].metric("Funções", metrics['num_functions'])
                        cols[2].metric("Classes", metrics['num_classes'])
                        cols[3].metric("Loops", metrics['num_loops'])
                        cols[4].metric("Condições", metrics['num_conditionals'])
    
    # =========================================================================
    # TAB 3 - AJUDA
    # =========================================================================
    with tab3:
        st.header("❓ Ajuda")
        
        st.markdown("""
        ### Como usar o Avaliador?
        
        1. **Escolhe um exercício** na tab "Avaliar Código"
        2. **Lê a descrição** para entender o que é pedido
        3. **Escreve o código** da função pedida
        4. **Clica em Avaliar** para ver o resultado
        
        ---
        
        ### Dicas
        
        - 🎯 A função deve ter **exatamente** o nome pedido
        - ✅ Testa primeiro com os exemplos mostrados
        - ⚠️ Não uses `import os`, `eval()`, `exec()` ou `open()`
        - 📝 Mantém o código limpo e legível
        
        ---
        
        ### Sistema de Pontuação
        
        | Componente | Peso |
        |------------|------|
        | Testes corretos | 80% |
        | Base | 20% |
        | Penalização segurança | -10 por problema |
        | Penalização estilo | -2 por problema (max -10) |
        
        **Aprovação:** ≥ 50 pontos
        
        ---
        
        ### Exercícios Disponíveis
        """)
        
        exercises = list_exercises()
        for ex in exercises:
            st.markdown(f"- **{ex.get('title')}** (`{ex['id']}`) - `{ex.get('function')}()`")


if __name__ == "__main__":
    main()
